from enum import Enum
import shutil
import time
import sys
import io

class DisplayType(Enum):
    BOTTOM_UP = 'from_bottom'
    STATIC = 'from_top'



class Display:
    def __init__(self, renderMethod: DisplayType, max_log_lines=10, width=100):
        
        self.renderMethod = renderMethod
        self.max_log_lines = max_log_lines
        self.log = []
        self.width = width
        self.current_lines = 0
        self.buffer = io.StringIO()
        self.last_update = time.time_ns()
        self.delta_time = self.get_delta_time()

        self.header_template = [
            'Rate of Progress',
            'Profiles in queue                   {queue_length}',
            'Queue clearing rate:                {queue_clearing_rate:3.2f} profiles/sec',
            'Queue finished in:                  {queue_clearing_time} sec',
            'Database Stats',
            'Profiles in db:                     {profiles_in_db}',
            'Profiles with friends:              {profiles_with_friends}',
            'Profiles without friendslist:       {profiles_without_friends}',
            'Profiles with less then 10 friends: {profiles_with_less_than_10_friends}',        
        ]

        self.header_data = {
            'queue_length': 1,
            'queue_clearing_rate': 1,
            'queue_clearing_time': 1,
            'profiles_in_db': 1,
            'profiles_with_friends': 1,
            'profiles_without_friends': 1,
            'profiles_with_less_than_10_friends': 1,
        }
        self.header_lines = len(self.header_template) + 1
        self.initialized = False

    def get_delta_time(self):
        current_time = time.time_ns()
        self.delta_time = current_time - self.last_update
        self.last_update = current_time
        return self.delta_time
    
    def add_log(self, message: str):
        if self.renderMethod == DisplayType.BOTTOM_UP:
            self.log.insert(0, message)
            self.render()
        elif self.renderMethod == DisplayType.STATIC:
            self.log.append(message)
            if len(self.log) > self.max_log_lines:
                self.log.pop(0)

    def update_header_data(self, data: dict):
        prev_queue_length = self.header_data['queue_length']
        updates = {
            'queue_length': data.get('queue_length', self.header_data.get('queue_length', 0)),
            'profiles_in_db': data.get('profiles_in_db', self.header_data.get('profiles_in_db', 0)),
            'profiles_with_friends': data.get('profiles_with_friends', self.header_data.get('profiles_with_friends', 0)),
            'profiles_without_friends': data.get('profiles_without_friends', self.header_data.get('profiles_without_friends', 0)),
            'profiles_with_less_than_10_friends': data.get('profiles_with_less_than_10_friends', self.header_data.get('profiles_with_less_than_10_friends', 0)),
        }
        if 'queue_length' in data:
            updates['queue_clearing_rate'] = (prev_queue_length - data['queue_length']) / ((self.get_delta_time()/1e9)+1e-9)
            updates['queue_clearing_time'] = data['queue_length']*(updates['queue_clearing_rate']+1e-9)
        
        self.header_data.update(updates)

    def render(self):
        if self.renderMethod == DisplayType.BOTTOM_UP:
            self.render_bottom_up()
        elif self.renderMethod == DisplayType.STATIC:
            self.render_static()
            
    def render_static(self):
        self.max_log_lines = shutil.get_terminal_size().lines - self.header_lines - 1

        if not hasattr(self, 'initialized') or not self.initialized:
            self.current_lines = len(self.header_template) + 1 + self.max_log_lines
            print('\n'*(self.current_lines-1))
            self.initialized = True
        
        # Hide the cursor
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        
        sys.stdout.write(f'\033[{self.current_lines}A')
        self.current_lines = 0

        for template in self.header_template:
            line = template.format(**self.header_data)
            print(f'{line: <{self.width}}', end='\r\n')
            self.current_lines += 1
        
        print('-'*self.width)
        self.current_lines += 1

        for i in range(self.max_log_lines):
            line = self.log[i] if i < len(self.log) else ''
            print(f'{line:<{self.width}}', end='\r\n')
            self.current_lines += 1

        sys.stdout.flush()

        # Show the cursor again (optional, omit if you want it hidden permanently)
        # sys.stdout.write("\033[?25h")
        # sys.stdout.flush()

    def render_bottom_up(self):
        

        sys.stdout.write("\033[?25l")
        if self.log:
            self.buffer.write(f'{self.log.pop(): <{self.width}}\r\n')
        self.buffer.write(f'{' ': <{self.width}}\r\n')

        for template in self.header_template:
            line = template.format(**self.header_data)
            self.buffer.write(f'{line: <{self.width}}\r\n')

        finalStatement = self.buffer.getvalue()
        sys.stdout.write(finalStatement)
        self.buffer.truncate(0)
        self.buffer.seek(0)

        sys.stdout.write(f"\033[{len(self.header_template)+1}A")
        sys.stdout.flush()