import datetime

from PyQt5.QtCore import QThread, QAbstractTableModel, QModelIndex, Qt, QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QDialog, QTableWidgetItem, QAbstractScrollArea, QHeaderView
from PyQt5.QtWidgets import QMainWindow

import client

from ui_clientform import Ui_DigitizationClient

from ui_sessionform import Ui_SessionForm

# table column indexes
SEQUENCE, BARCODE, FILENAME, TIME, STATUS = range(5)
# status colors
WARNING_COLOR = QColor(255, 150, 150)


class SessionForm(QDialog):
    def __init__(self, parent=None, technicianName=None, collectionCode=None, projectCode=None, taxa=None, notes=None, station_code=None):
        super(SessionForm, self).__init__(parent)
        self.ui = Ui_SessionForm()
        self.ui.setupUi(self)
        self.technicianName = technicianName
        self.collectionCode = collectionCode
        self.projectCode = projectCode
        self.taxa = taxa
        self.notes =  notes
        self.station_code = station_code
        # populate form
        # TODO get existing values if any and set text/combo box
        #self.ui.technicianNameLineEdit.setText(self.technicianName)
        self.exec_()

    # https://stackoverflow.com/a/11553456/560798
    def accept(self):
        self.collectionCode = self.ui.collectionCodeComboBox.currentText()
        self.technicianName = self.ui.technicianNameLineEdit.text()
        self.projectCode = self.ui.projectCodeComboBox.currentText()
        self.taxa = self.ui.taxaLineEdit.text()
        self.notes = self.ui.plainTextNotes.toPlainText()
        self.station_code = self.ui.stationCodeLineEdit.text()
        super(SessionForm, self).accept()


class ClientForm(QMainWindow):
    def __init__(self, parent=None):
        super(ClientForm, self).__init__(parent)
        self.ui = Ui_DigitizationClient()
        self.ui.setupUi(self)
        self.model = SessionTableModel()
        self.ui.tableView.setModel(self.model)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui) # primarily used to update the elapsed time and rate
        self.timer.start(1000)
        #TEST setting column width and scroll area
        #self.ui.tableView.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        #self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #ResizeToContents
        #self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        #self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.setStretchLastSection(True))
        self.session = None
        self.session_collectionCode = None
        self.session_technicianName = None
        self.session_projectCode = None
        self.sessionStartTime = None
        self.session_notes = None
        self.session_taxa = None
        self.session_station_code = None
        # manual slot connection
        self.ui.buttonSessionPath.clicked.connect(self.showSessionPathDialog)
        self.ui.buttonSessionData.clicked.connect(self.showSessionDialog)
        self.ui.buttonStartSession.clicked.connect(self.startSession)
        self.ui.buttonEndSession.clicked.connect(self.endSession)
        # create emitter to be used by client.py
        self.emitter_inst = Emitter()
        self.emitter_inst.event_triggered.connect(self.update_table_view)

    def test(self):
        print('Emitter worked, TEST')

    def update_ui(self):
        self.update_time()
        self.update_rate()
        self.update_image_count()

    def update_time(self):
        # display elapsed session time in UI
        if self.session:
            elapsed_time = self.session.elapsed_time()
            if elapsed_time:
                hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                #elapsed_time_str = str(int(hours)) + ':' + str(int(minutes)) + ':' + str(int(seconds))
                elapsed_time_str = f"{int(hours)}:{int(minutes)}:{int(seconds)}"
                self.ui.labelElapsedTime.setText(elapsed_time_str)

    def update_rate(self):
        # display imaging rate in UI
        if self.session:
            imaging_rate = self.session.imaging_rate()
            if imaging_rate:
                #self.ui.labelRate.setText(str(imaging_rate))
                self.ui.labelRate.setText(f"{imaging_rate:.1f}")

    def update_image_count(self):
        # display imaging rate in UI
        if self.session:
            image_count = len(self.session.image_events)
            if image_count:
                #self.ui.labelRate.setText(str(imaging_rate))
                self.ui.labelImageCount.setText(str(image_count))

    def add_event(self, event=None):
        """
        called from client.py
        Adds new event to the GUI table model
        Refreshes table display after data changes
        """
        if self.session:
            if event:
                # Populate session metadata for event
                event.collection_code = self.session_collectionCode
                event.creator = self.session_technicianName
                event.project_code = self.session_projectCode
                # Sequential number for event
                self.session.event_number += 1
                event.sequence = self.session.event_number
                print('EVENT SEQ:', event.sequence)
                # Add event to GUI model
                # self.model.image_events.append(event)
                # Adding event to start of list so it sorts in table
                # TODO - sort the table view instead of the list
                self.model.image_events.insert(0, event)
                print('updating table')
                # TEST sorting
                #self.ui.tableView.sort(1, 0) #descending
                #self.ui.tableView.sortByColumn(1, 1) #descending
                #self.ui.tableView.model.sortByColumn(1, 0) #descending
                # END sorting
                self.ui.tableView.model().layoutChanged.emit()
                self.ui.tableView.resizeColumnsToContents()
                self.emitter_inst.update()
            else:
                print('No event passed.')
        else:
            print('No session started, can not add event')

    # @pyqtSlot()
    def update_table_view(self):
        # Test slot used to activate the real slot
        print('update_table_view')
        self.ui.tableView.model().layoutChanged.emit()

    def startSession(self):
        self.session = client.Session(client_ui=self)
        print('session.uuid:', self.session.uuid)
        # Add session metadata from UI
        self.session.collection_code = self.session_collectionCode
        self.session.username = self.session_technicianName
        self.session.project_code = self.session_projectCode
        self.session.notes = self.session_notes
        self.session.taxa = self.session_taxa
        self.session.station_code = self.session_station_code
        self.session.path = self.sessionPath
        self.session.event_number = 0 # sequential number for ordering events in list
        if self.session.path:
            self.monitorSession = monitorSessionThread()
            # pass objects to be used in thread
            self.monitorSession.set_session(session=self.session)
            self.monitorSession.start()
            self.ui.buttonStartSession.setEnabled(False)
            # self.session.start_time isn't being set in time to be registered below?
            start_time = datetime.datetime.now() # time according to UI thread, not actual time from session object.
            self.ui.sessionStatusLineEdit.setText('Session started: ' + str(start_time))
        else:
            print('No valid session path.')
            self.ui.sessionStatusLineEdit.setText('Invalid path.')

    def endSession(self):
        print('Ending session.')
        self.timer.stop()

    def showSessionPathDialog(self):
        sessionPath = QFileDialog.getExistingDirectory(self, 'Select session folder', '/home')
        if sessionPath:
            # TODO confirm that path is valid and writeable
            self.sessionPath = os.path.abspath(sessionPath)
            self.ui.sessionPathLineEdit.setText(os.path.abspath(sessionPath))

    def showSessionDialog(self):
        sessionDialog = SessionForm()
        if sessionDialog.result() == QDialog.Rejected:
            # set to previous values?
            print("sessionDialog rejected")
        else:
            # get values set in form
            collectionCode = sessionDialog.collectionCode
            technicianName = sessionDialog.technicianName
            projectCode = sessionDialog.projectCode
            taxa = sessionDialog.taxa
            notes = sessionDialog.notes
            station_code = sessionDialog.station_code
            # Store values to save in session once it is initialized
            self.session_collectionCode = collectionCode
            self.session_technicianName = technicianName
            self.session_projectCode = projectCode
            self.session_taxa = taxa
            self.session_notes = notes
            self.session_station_code = station_code
            # Write to UI
            sessionDataText = ''
            sessionDataText += 'Name: ' + technicianName + '\n'
            sessionDataText += 'Collection code: ' + collectionCode + '\n'
            sessionDataText += 'Project code: ' + projectCode + '\n'
            sessionDataText += 'Station code: ' + station_code + '\n'
            sessionDataText += 'Taxa: ' + taxa + ' Notes: ' + notes
            self.ui.sessionDataTextBrowser.setText(sessionDataText)

class monitorSessionThread(QThread):

    def __init__(self):
        QThread.__init__(self)
        self.sessionPath = None
        self.session = None

    def __del__(self):
        self.wait()

    def set_session_path(self, sessionPath=None):
        #print('in set_session_path', sessionPath)
        if sessionPath:
            self.sessionPath = sessionPath

    def set_session(self, session=None):
        #print('in set_session', session)
        if session:
            self.session = session

    def run(self):
        if self.session.path:
            #print('thread: session.start()')
            self.session.start()
        else:
            print('No session path in thread.')
            self.terminate


class Emitter(QObject):
    event_triggered = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)

    def update(self):
        # event was updated or created
        print('Emitter emitting update')
        self.event_triggered.emit()


class SessionTableModel(QAbstractTableModel):

    def __init__(self):
        super(SessionTableModel, self).__init__()
        self.image_events=[]

    def rowCount(self, index=QModelIndex()):
        return(len(self.image_events))

    def columnCount(self, index=QModelIndex()):
        return 5

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        event = self.image_events[index.row()]
        # SEQUENCE, BARCODE, FILENAME, TIME, STATUS
        if role == Qt.DisplayRole:
            if column == SEQUENCE:
                return event.sequence
            if column == BARCODE:
                return event.catalog_number
            elif column == FILENAME:
                return event.original_filename
            elif column == TIME:
                return event.raw_image_creation_date
            elif column == STATUS:
                return event.status
        # Background color:
        # https://stackoverflow.com/a/44104745/560798
        if role == Qt.BackgroundRole:
            #if QSqlQueryModel.data(self, self.index(item.row(), 2), Qt.DisplayRole) == "Young":
            #    return QBrush(Qt.yellow)
            if column == STATUS:
                status_string = self.data(index=index, role=Qt.DisplayRole)
                # print('status_string:', status_string)
                if 'WARNING' in status_string:
                    return QBrush(Qt.red)
                if 'Raw' in status_string:
                    #return QBrush(Qt.green)
                    return QBrush(WARNING_COLOR)


                #if self.data(index=index, role=Qt.DisplayRole) == "Young":
                # return QBrush(Qt.yellow)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            return int(Qt.AlignRight | Qt.AlignVCenter)
        if role != Qt.DisplayRole:
            return None
        # BARCODE, FILENAME, TIME, STATUS
        if orientation == Qt.Horizontal:
            if section == SEQUENCE:
                return "#"
            if section == BARCODE:
                return "Barcode"
            elif section == FILENAME:
                return "Filename"
            elif section == TIME:
                return "Time"
            elif section == STATUS:
                return "Status"
        return int(section + 1)


    def sort(self, Ncol, order):
        #Sort table by given column number.
        self.layoutAboutToBeChanged.emit()
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.layoutChanged.emit()


"""
    # from https://www.saltycrane.com/blog/2007/12/pyqt-43-qtableview-qabstracttablemodel/
    def sort(self, Ncol, order):
        #Sort table by given column number.
        #self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.layoutChanged.emit()
        #self.emit(SIGNAL("layoutChanged()"))
"""


if __name__ == '__main__':
    import sys
    import os

    app = QApplication(sys.argv)
    client_ui = ClientForm()
    client_ui.show()
    #sys.exit(app.exec_())
    ret = app.exec_()
    # cleanup
    # see https://stackoverflow.com/a/3833075/560798 - solution for keeping UI active until close
    client_ui.session.end_session()
    sys.exit(ret)
