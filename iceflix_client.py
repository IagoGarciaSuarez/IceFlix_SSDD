#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import cmd
import os
from datetime import datetime
import json

ICEFLIX_BANNER = """
  ___         _____ _ _      
 |_ _|___ ___|  ___| (_)_  __
  | |/ __/ _ \ |_  | | \ \/ /
  | | (_|  __/  _| | | |>  < 
 |___\___\___|_|   |_|_/_/\_\
                             
"""

class WorkTime(cmd.Cmd):
    def __init__(self, x):
        self.x = x
    prompt = '> '
    intro = ICEFLIX_BANNER + '\nEscribe \'help\' o \'?\' para mostrar los comandos disponibles.\n'
    
    def do_login(self, initial=None):
        'login - Inicia sesión una vez indicado un usuario y contraseña correctos.\n'
        print(self.x)
        
    def do_newproject(self, argv, initial=None):
        'newproject <project> - Creates a new project given a name. To start counting work time type \'start <project>\'.\n'
        if not argv:
            print('[ERROR] No project given. Check \'help newproject\' for more info.\n')
        else:
            self.file = argv + '.wt'
            with open(self.file, 'w+') as f:
                self.wtData = {'star_time': 'total_time'}
                json.dump(self.wtData, f) 
                f.close()   
            print(f'[INFO] New project created. To start counting work time type \'start {argv}\'.\n')
        if self.recording:
            print(f'[REMINDER] Currently counting worktime in {splitext(self.file)[0]}. Type \'stop\' to stop the count.\n')


    def do_removeproject(self, argv, initial=None):
        'removeproject <project> - Removes a project by name. Needs confirmation.\n'
        if not argv:
            print('[ERROR] No project given. Check \'help removeproject\' for more info.\n')
        else:
            self.file = argv + '.wt'
            if not self.recording:
                if isfile(self.file):
                    if input(f'[CONFIRMATION] Are you sure you want to delete worktime data form project named \'{self.file}\'? (y/n)\n>') == 'y':
                        os.remove(self.file)
                        print(f'[INFO] Worktime data from {argv} removed successfully.\n')
                    else:
                        print('[INFO] Project deletion cancelled.\n')
                else:
                    print(f'[ERROR] No worktime file found with name {self.file}\n')
            else:
                print(f'[REMINDER] Currently counting worktime in {splitext(self.file)[0]}. Type \'stop\' to stop the count.\n')


    def do_listprojects(self, initial=None):
        'listprojects - Lists all projects in the current directory.\n'
        for self.file in os.listdir("."):
            if self.file.endswith(".wt"):
                print(splitext(self.file)[0])

    def do_stop(self, initial=None):
        'stop - Stops current worktime count and saves it to the project worktime data.\n'
        if not self.recording:
            print('[ERROR] No project worktime is active. Type \'help stop\' for more info.\n')
        else:
            total_time = datetime.strptime(datetime.today().strftime(TIME_FORMAT), TIME_FORMAT) - datetime.strptime(self.start_time, TIME_FORMAT)
            print(f'[INFO] Worktime counted for this last session in {splitext(self.file)[0]}: {total_time}\n')
            with open(self.file, 'w') as f:
                self.wtData[self.start_time] = str(total_time)
                json.dump(self.wtData, f)
                f.close()

            self.recording = False

    def do_exit(self, initial=None):
        'exit - Stop and exit WorkTime'
        return self.close()

    def close(self):
        self.do_stop()
        return True


if __name__ == "__main__":
    wt = WorkTime(x='hehe')
    try:
        wt.cmdloop()
    except KeyboardInterrupt:
        wt.close()
