import xml.etree.ElementTree as ET
import re
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import os

#%% TODO
# Screen for bad arrows, make sure they have both source and target.
# When adding event components, check to make sure title is right and such?

#%% Defines.
# Base structure of an event.
EVENT_BASE = '''
# event_name
province_event = {
\tid = diggy_dungeons.event_ID
\ttitle = diggy_dungeons.event_ID.t
desc_placeholder
\tpicture = TRADEGOODS_eventPicture
	
\tis_triggered_only = yes
	
\ttrigger = {
\t\thas_province_flag = sent_expedition_@owner
\t}
options_placeholder
}
'''

# Desc regular.
DESC_SINGLE = '\tdesc = diggy_dungeons.event_ID.d'

# Desc multiple.
DESC_MULTIPLE = '''\tdesc = {
\t\ttrigger = { always = yes }
\t\tdesc = diggy_dungeons.event_ID.d.1
\t}
\tdesc = {
\t\ttrigger = { always = no }
\t\tdesc = diggy_dungeons.event_ID.d.2
\t}
'''

# Base structure of an option.
OPTION_BASE = '''
\toption = {
\t\tname = diggy_dungeons.event_ID.option_ID
\t\tai_chance = { factor = 100 }
\t\ttrigger = {
\t\t\talways = yes
\t\t}
event_effects
\t}'''

# Base structure of party statistics change.
PARTY_BASE_CHANGE_ADD = '\t\tchange_party_stat = { add_tooltip = yes add = value }\n'

# Party attributes and their default change values.
PARTY_DEFAULT_DELTA = { 
    'loot': 75,
    'morale': 0.5,
    'manpower': 200,
    'supplies': 4, 
    'effectiveness': 5,    
    'party_rewards': 50
}

# Changing a variable value
VARIABLE_CHANGE_BASE = '\t\tchange_variable = { which = variable_name value = value_change }\n'

# ADK effect
ADK_EFFECT = '\t\tadd_adk_effect = { add = value_change }\n'

# Dungeon progress.
PROGRESS_BASE = '\n\t\tdungeon_progress_advancement = { id = progress_ID } # #&progress_ID'

# Encounter effect.
ENCOUNTER_EFFECT_BASE = '''		
\t\tdungeon_encounter_effect = {
\t\t\tbase_success = success_chance
\t\t\tsuccess_id = success_target # #&success_target
			
\t\t\tbase_failure = failure_chance
\t\t\tfailure_id = failure_target # #&failure_target
\t\t}'''

# Game over string.
GAME_OVER_STRING = '''
        custom_tooltip = expedition_dead_tooltip
        hidden_effect = { expedition_dead_effect = yes }
'''

# Supplies.
SUPPLIES_CHECK = 'check_variable = { partySupplies = value }'

# Initial event string.
START_EVENT_STRING = '''
# Misc event presenting what the dungeons is
province_event = {
\tid = diggy_dungeons.event_ID
\ttitle = diggy_dungeons.event_ID.t
\tdesc = diggy_dungeons.event_ID.d
\tpicture = CAVE_eventPicture
    
\tis_triggered_only = yes
    
\ttrigger = {
\t\talways = yes
\t}
    
\timmediate = {
\t}
    
\tafter = {
\t}
    
\t# Nice
\toption = {
\t\tname = diggy_dungeons.event_ID.a
\t\tai_chance = { factor = 100 }
\t}
}
'''

# End event string.
END_EVENT_STRING = '''
\timmediate = {
\t\tdungeon_immediate_effect = yes
\t}

\toption = {
\t\tname = diggy_dungeons.event_ID.a
\t\tai_chance = { factor = 100 }
\t\ttrigger = {
\t\t    always = yes
\t\t}
\t\tspecial_reward_expedition = yes
\t\tcurrency_effect_expedition = {  currency = treasury cash = yes addTo = owner }
\t\tcurrency_effect_expedition = {  currency = adm_power mana = yes addTo = owner }
\t\tcurrency_effect_expedition = {  currency = dip_power mana = yes addTo = owner }
\t\tcurrency_effect_expedition = {  currency = mil_power mana = yes addTo = owner }
\t\thidden_effect = {
\t\t\twhile = {
\t\t\t\tlimit = { check_variable = { partyManpower = 1000 } }
\t\t\t\tsubtract_variable = { partyManpower = 1000 }
\t\t\t\towner = { add_manpower = 1 }
\t\t\t}
\t\t}
\t\tcustom_tooltip = back_to_manpower_tooltip
\t\tcustom_tooltip = base_expedition_loot_tooltip
\t\tif = {
\t\t\tlimit = { check_variable = { ancientDwarvenKnowledge = 1 } }
\t\t\tprovince_event = { id = diggy_expedition.14 }
\t\t}
\t\telse = { hidden_effect = { clear_expedition_effect = yes } }
\t\thidden_effect = { set_province_flag = floor_explored }\t}
'''

# Localization structure.
LOCALIZATION_BASE = ' diggy_dungeons.event_ID.loc_ID:0 "Text"\n'


# Hex color identities.
HEX_COLORS_LIST = ['#e1d5e7', '#d5e8d4', '#f8cecc', '#ffe6cc']
HEX_COLORS_DICT = {
    '#e1d5e7': 'Room',
    '#d5e8d4': 'Success',
    '#f8cecc': 'Failure',
    '#ffe6cc': 'End',
}

# Indicators for multiple descriptions and supplies being required for an option.
MULTIPLE_DESC = 'fillColor=#fff2cc'
OPTION_SUPPLIES_REQ = 'fillColor=#dae8fc'

# Success chances.
SUCCESS_CHANCE = {
    'E': 80,
    'M': 60,
    'H': 40
}

#%% Classes for the dungeon structure.
class Dungeon:
    def __init__(self, name, XML_string, ID_start: int, party_statistics_delta, debug = False):
        self.XML_string = XML_string
        self.name = name
        self.ID_start = ID_start
        self.party_statistics_delta = party_statistics_delta
        self.debug = debug
        
        if not debug:
            self.get_elements()
            self.get_events()
            self.get_floors()
            self.event_ID_dictionary()
            self.error_check()
            
        
    def __repr__(self):
        return f'{type(self).__name__}: {self.name}'
    
    # Extracts the elements from the XML file.
    def get_elements(self):
        tree = ET.ElementTree(ET.fromstring(self.XML_string))
        root = tree.getroot()
        self.elements = [root[0][0][0][i] for i in range(len(root[0][0][0]))]
        self.sub_elements = [0] * len(self.elements)
        for i in range(len(root[0][0][0])):
            try:
                self.sub_elements[i] = root[0][0][0][i][0]
            except:
                pass
        
    
    # Extracts the events from the elements.
    def get_events(self):
        self.events_dict = {}
        self.events_components = {}
        
        # Loops through each element and picks out elements which is a group, 
        # in which case it established as an event object and saved in a 
        # dictionary, or is a child of an event, in which case it is added to
        # that event as a  component.
        for element,sub_element in zip(self.elements, self.sub_elements):
            keys = element.keys()
            attribs = element.attrib
            if 'style' in keys:
                if 'group' in attribs['style']: # Not = 'group' due to some groups being rotated. Somehow.
                    self.events_dict[attribs['id']] = Event(element, sub_element, self)
                elif attribs['parent'] in self.events_dict and 'source' not in keys:
                    self.events_dict[attribs['parent']].add_component(element, sub_element)
                    self.events_components[attribs['id']] = self.events_dict[attribs['parent']]
                    
        
        # Check whether an element is an arrow. If so, establish a
        # connection between the target and the source. 
        for element in self.elements:
            keys = element.keys()
            attribs = element.attrib
            if 'source' in keys:
                # Print an error message if the arrow has no target.
                if 'target' not in keys:
                    print('Issue with arrow %s.' % attribs['id'])
                else:
                    source_opt      = attribs['source']
                    source_event    = self.events_components[source_opt]
                    target          = self.events_components[attribs['target']]
                    
                    source_event.add_connection(source_opt,target)
    
        # Saves the events to the dungeon class.
        self.events = [v for k,v in self.events_dict.items()]
        
    # Splits the events into floors.
    def get_floors(self):
        self.floors = []
        self.level = 0
        self.event_IDs = self.ID_start

        for event in self.events:
            if not hasattr(event, 'is_in_floor'):
                self.top_event = event
                self.floor_set_top_event()
                self.floor_get_events()
        
        # Makes sure that the floors are in correct order.
        self.floors_order()
                
        for floor in self.floors:
            self.floor_set_IDs(floor)

    # Looks for incoming connections to an event. If there is at least one, go
    # to the first incoming connection and repeat the process.
    def floor_set_top_event(self):
        while len(self.top_event.connections_in) > 0:
            self.top_event = self.top_event.connections_in[0]
    
    def floors_order(self):
        if len(self.floors) != 3:
            print('Dungeon does not have 3 floors. Something went wrong.')
        else:
            x_pos = [int(self.floors[i].events[0].xml_sub_element.attrib['x']) for i in range(3)]
            while x_pos[0] > x_pos[1]:
                x_pos[0], x_pos[1] = x_pos[1], x_pos[0]
                self.floors[0], self.floors[1] = self.floors[1], self.floors[0]
                while x_pos[1] > x_pos[2]:
                    x_pos[1], x_pos[2] = x_pos[2], x_pos[1]
                    self.floors[1], self.floors[2] = self.floors[2], self.floors[2]
            self.floors[0].level = 1
            self.floors[1].level = 2
            self.floors[2].level = 3
    
    # Gets all events flowing from a top event.
    def floor_get_events(self, debug = False):
        floor_events = [self.top_event]
        self.top_event.is_in_floor = True
        for event in floor_events:
            for connection_out in event.connections_out:
                if connection_out not in floor_events:
                    floor_events.append(connection_out)
                    connection_out.is_in_floor = True
            
        if debug:
            print(floor_events)                
        
        if len(floor_events) > 0:
            self.level += 1
            self.floors.append(Floor(self,self.level,floor_events))    

    # Assigns event IDs to all events in a floor.
    def floor_set_IDs(self, floor):
        for event in floor.events:
            self.event_IDs += 1
            event.event_ID = self.event_IDs
            

    def event_ID_dictionary(self):
        self.event_ID_dict = {}
        for event in self.events:
            self.event_ID_dict[event.event_ID] = event

    # Some possible issues.
    def error_check(self):
        for event in self.events:
            # No event should be without any connections at all.
            if len(event.connections_out) == 0 and len(event.connections_in) == 0:
                print(f'{event.ID} has no connections! {event.title} {event.desc}')
            # Every event should have a title, a description, and at least
            # one option.
            if event.title == None:
                print(f'{event} has no title element!')
            if event.desc == None:
                print(f'{event} has no description element!')
            if event.options == []:
                print(f'{event} has no option element!')
            # An event should be one of four types.
            if not hasattr(event, 'type'):
                print(f'{event} has no type!')
                
    # Writes to output files.
    def write_to_file(self,file_name):
        # Event file.
        with open(f'{file_name}.txt', 'w') as file:
            file.write(f'Dungeon: {self.name}\n')            
            file.write(START_EVENT_STRING.replace('event_ID', str(self.ID_start)))
            for floor in self.floors:
                file.write(f'# {str(floor)}')
                for event in floor.events:
                    event.write_event(file)     

        # Kinda stupid but easy way to get rid of .0s in the event file, which 
        # cause issues in the game for some reason.
        with open(f'{file_name}.txt', 'r') as file:
            lines = file.readlines()
        with open(f'{file_name}.txt', 'w') as file:
            for line in lines:
                line = line.replace(".0", "")
                
                # Also adds in names for events.
                if '#&' in line:
                    event_ID = int(line.split('#&')[1].strip())
                    event_name = str(self.event_ID_dict[event_ID])
                    line = line.replace(f'#&{event_ID}',event_name)

                file.write(line)
                    
                    
        
        # Localization file.
        with open(f'{file_name}.yml', 'w') as file:
            file.write('l_english:\n')
            file.write(f' diggy_dungeons.{self.ID_start}.t:0 ""\n')
            file.write(f' diggy_dungeons.{self.ID_start}.d:0 ""\n')
            file.write(f' diggy_dungeons.{self.ID_start}.a:0 ""\n')
            file.write('\n')
            for floor in self.floors:
                for event in floor.events:
                    event.title.write_loc(file)
                    event.desc.write_loc(file)
                    for option in event.options:
                        option.write_loc(file)
                    file.write('\n')

# Floor class, mostly serving as a container for the events within it.
class Floor:
    def __init__(self, parent, level, events):
        self.parent = parent
        self.level  = level
        self.events = events

    def __repr__(self):
        return f'{self.parent.name} floor {self.level}'

class Event:
    def __init__(self, xml_element, xml_sub_element, dungeon):
        self.xml_element = xml_element
        self.xml_sub_element = xml_sub_element
        self.dungeon = dungeon
        self.ID = xml_element.attrib['id']
        self.title = None
        self.desc = None
        self.options = []
        self.components = []
        self.connections_in  = []
        self.connections_out = []
        self.type = None
        
    def __repr__(self):
        if self.type in ['Success', 'Failure']:
            return f'{self.connections_in[0]}: {self.origin.text} - {self.type}'
        elif self.title != None:
            return f'{self.title.text}'
        else:
            return f'{self.ID}'
        
    def add_component(self,xml_element, xml_sub_element):
        component_width = int(xml_sub_element.attrib['width'])
        
        # If the width is 100, the component is a description.
        if component_width == 100:
            self.desc = Desc(xml_element, xml_sub_element, self)

        # Otherwise it should be 120.
        elif component_width == 120:
            # Checks whether the subelement has a y value. If so, it's an option.
            if 'y' in xml_sub_element.attrib:
                self.options.append(Option(xml_element, xml_sub_element, self))                
            else:
                self.title = Title(xml_element, xml_sub_element, self)

        # Something has gone wrong it it's not one of those two.
        else:
            print(f'Error at {xml_element}.')

    # Adds connections between events, as well as for the option leading to 
    # the target event. If an option leads to Success and Failure events, then
    # they are additionally added as success and failure attributes.
    def add_connection(self,source,target):
        for option in self.options:
            if option.ID == source:
                option.outcomes.append(target)
                target.origin = option
                if target.type == 'Success':
                    option.success = target
                    option.get_difficulty()
                elif target.type == 'Failure':
                    option.failure = target
        self.connections_out.append(target)
        target.connections_in.append(self)

    # Generates the event code.
    def write_event(self,file):
        if self.desc.multiple_desc:
            desc = DESC_MULTIPLE
        else:
            desc = DESC_SINGLE
        
        self.event_string = EVENT_BASE.replace('desc_placeholder', desc)\
                                      .replace('event_name', str(self))\
                                      .replace('event_ID', str(self.event_ID))
        
        # Adds code from options.
        options_string = ''
        for option in self.options:
            option.write_option()
            options_string += option.option_string
        
        if self.type == 'End':
            options_string = END_EVENT_STRING.replace('event_name', str(self))\
                                             .replace('event_ID', str(self.event_ID))
        
        self.event_string = self.event_string.replace('options_placeholder', options_string)
        
        file.write(self.event_string)

class EventComponent:
    def __init__(self, xml_element, xml_sub_element, parent):
        self.xml_element = xml_element
        self.xml_sub_element = xml_sub_element
        self.ID = xml_element.attrib['id']
        self.text = xml_element.attrib['value']
        self.parent = parent
        parent.components.append(self)
        # Various additional setup unique to each event component.
        self.extra_setup()
    
    def __repr__(self):
        return f'{self.parent.event_ID} {type(self).__name__}: {self.text}'

            
class Title(EventComponent):
    def extra_setup(self):
        self.loc_ID = 't'
        style = self.xml_element.attrib['style']
        color = re.findall(r'(?<=fillColor=)+.{7}',style)[0]
        self.parent.type = HEX_COLORS_DICT[color]

    # Writing the localization string to an output file.
    def write_loc(self, file):
        loc_string = LOCALIZATION_BASE.replace('event_ID', str(self.parent.event_ID))
        loc_string = loc_string.replace('loc_ID', str(self.loc_ID))
        loc_string = loc_string.replace('Text', str(self.parent))
        
        file.write(loc_string)

class Desc(EventComponent):
    def extra_setup(self):
        self.loc_ID = 'd'
        if MULTIPLE_DESC in self.xml_element.attrib['style']:
            self.multiple_desc = True
        else:
            self.multiple_desc = False

    # Writing the localization string to an output file.
    def write_loc_desc(self, file, extra):
        loc_string = LOCALIZATION_BASE.replace('event_ID', str(self.parent.event_ID))
        loc_string = loc_string.replace('loc_ID', str(self.loc_ID) + extra)
        loc_string = loc_string.replace('Text', self.text)
        
        file.write(loc_string)

    # Writing the localization string to an output file.
    def write_loc(self, file):
        if self.multiple_desc:
            self.write_loc_desc(file, '.1')
            self.write_loc_desc(file, '.2')
        else:
            self.write_loc_desc(file, '')

class Option(EventComponent):
    def __repr__(self):
        return f'{self.parent} {type(self).__name__} {self.loc_ID}: {self.text}'

    def extra_setup(self):
        self.index = len(self.parent.options)
        if self.index > 3: # If the index is 4 it will correspond to the letter
                           # d, which is reserved for the description.
            self.index += 1
        self.loc_ID = chr(ord('a') + self.index)
        self.outcomes = []
        if OPTION_SUPPLIES_REQ in self.xml_element.attrib['style']:
            self.supplies_req = True
        else:
            self.supplies_req = False
    
    # Computes the base success of an option based on its text. Should always
    # be a value corresponding to an entry in the SUCCESS_CHANCE table or a 
    # raw number.
    def get_difficulty(self):
        if '(' in self.text:
            self.difficulty = self.text.split('(')[1].split(')')[0]
            if self.difficulty in SUCCESS_CHANCE:
                self.base_succes = SUCCESS_CHANCE[self.difficulty]
            else:
                try:
                    self.base_succes = int(self.difficulty)
                except:
                    self.base_succes = SUCCESS_CHANCE['E']
                    print(f'Something strange with difficulty in {self}.')                    
        else:
            self.base_succes = SUCCESS_CHANCE['E']
            print(f'No difficulty provided for {self}.')
    
    # Writing the localization string to an output file.
    def write_loc(self, file):
        loc_string = LOCALIZATION_BASE.replace('event_ID', str(self.parent.event_ID))
        loc_string = loc_string.replace('loc_ID', str(self.loc_ID))
        loc_string = loc_string.replace('Text', self.text)
        
        file.write(loc_string)
        
    # Generates the event code for an option.
    def write_option(self):
        party_statistics_delta = self.parent.dungeon.party_statistics_delta
        
        # Grabs base event string and inputs the event and option ID.
        self.option_string = OPTION_BASE.replace('event_ID', str(self.parent.event_ID))\
                                        .replace('option_ID', self.loc_ID)
        
        
        effect_string = ''

        # Checks whether an option needs supplies. If so, checks whether the
        # player has enough supplies, and adds an effect which removes the 
        # supplies in question.
        if self.supplies_req:
            supply_needed = SUPPLIES_CHECK.replace('value',str(party_statistics_delta['supplies']))
            self.option_string = self.option_string.replace('always = yes', supply_needed)
            
            change_string = PARTY_BASE_CHANGE_ADD.replace('stat', 'supplies')\
                                                 .replace('value', str(party_statistics_delta['supplies']))
            change_string = change_string.replace('add_tooltip', 'remove_tooltip')
            change_string = change_string.replace('add', 'loss')
            effect_string += change_string
        
        # Splits the option text by commas, then goes through each fragment
        # to get the amount of + or -, then generates the party change effect.
        # Also includes recognition of ADK.
        effect_fragments = self.text.split(',')
        for fragment in effect_fragments:
            fragment_string = fragment.replace(' ','')
            
            delta = 0
            
            # Finds number of plus/minus in fragment and adjusts delta.
            while '+' in fragment_string:
                fragment_string = fragment_string.replace('+','',1)
                delta += 1
            while '-' in fragment_string:
                fragment_string = fragment_string.replace('-','',1)
                delta += -1
            
            # The remaining should just be a keyword, which is then initialized.
            # Default party statistics.
            if fragment_string in party_statistics_delta:
                value = party_statistics_delta[fragment_string] * abs(delta)
                
                # Ensures that integer values are represented as such.
                if value == int(value):
                    value = int(value)
                
                change_string = PARTY_BASE_CHANGE_ADD.replace('stat', fragment_string)\
                                                     .replace('value', str(value))
                
                # If delta is negative, adjust the string.
                if delta < 0:
                    change_string = change_string.replace('add_tooltip', 'remove_tooltip')
                    change_string = change_string.replace('add', 'loss')
                
                # Adds the party statistics change to the effect string.
                effect_string += change_string
            # Alternative effects.
            elif fragment_string in ['ADK']:
                effect_string += ADK_EFFECT.replace('value_change', str(delta))
                    
        # Dungeon progress.
        if len(self.outcomes) == 1:
            progress_ID = self.outcomes[0].event_ID
            effect_string += PROGRESS_BASE.replace('progress_ID', str(progress_ID))
        
        # Encounter effect for when an option has two outcomes. One of them
        # should always be success or fail, but there might be cases where it
        # only has one of the two.
        if len(self.outcomes) == 2:
            # Check if there is a success event but no failure event. If so, try to find another
            # event outcome, and assign that as the failure event.
            if not hasattr(self,'failure'):
                for event in self.outcomes:
                    if event.type != 'Success':
                        self.failure = event
            if not hasattr(self,'success'):
                for event in self.outcomes:
                    if event.type != 'Failure':
                        self.success = event

            effect_string += ENCOUNTER_EFFECT_BASE.replace('success_chance', str(self.base_succes))\
                                                  .replace('success_target', str(self.success.event_ID))\
                                                  .replace('failure_chance', str(100 - self.base_succes))\
                                                  .replace('failure_target', str(self.failure.event_ID))
            
        if self.parent.title.text.lower() == 'game over':
            effect_string = GAME_OVER_STRING

        # Replaces the effects placeholder with the effects string.
        self.option_string = self.option_string.replace('event_effects', effect_string)
            
#%% Example execution with a bit of testing.
# dungeon = Dungeon('Ancient Library', data, 101)
# dungeon.write_to_file('test')

# print('')
# print('The following non-ending options have no outcomes:')
# for floor in dungeon.floors:
#     for event in floor.events:
#         if event.type != 'End' and event.title.text.lower() != 'game over':
#             for option in event.options:
#                 if option.outcomes == []:           
#                     print('Option {}.{} with the text {}'.format(event.event_ID,
#                                                                  option.loc_ID,
#                                                                  option.text))

# print('')
# print('The following events have no incoming connections:')
# for floor in dungeon.floors:
#     for event in floor.events:
#         if event.connections_in == []:
#             print('Event {} with the title {}'.format(event.event_ID,event.title.text))
# print('')            
# print('The following events have no outgoing connections:')
# for floor in dungeon.floors:
#     for event in floor.events:
#         if event.connections_out == []:
#             print('Event {} with the title {}'.format(event.event_ID,event.title.text))

#%% GUI class            
class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.select_image_file = ''
        self.select_music_file = ''
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        """Set up GUI"""
        self.run_script = tk.Button(self)
        self.run_script['text'] = 'Run Program'
        self.run_script['command'] = self.run_app
        self.run_script.pack(side='top', pady=5)

        self.output_text = tk.StringVar(value='Ready to run')
        self.output_label = tk.Label(self, textvariable=self.output_text)
        self.output_label['wraplength'] = 480
        self.output_label.pack(side='top', pady=5)

        self.dungeon_name_label = tk.Label(self)
        self.dungeon_name_label['text'] = 'Dungeon name'
        self.dungeon_name_label['wraplength'] = 170
        self.dungeon_name_label.pack(side='top', pady=5)
        self.dungeon_name = tk.Entry(self)
        self.dungeon_name.pack(side='top', pady=5)

        self.start_ID_label = tk.Label(self)
        self.start_ID_label['text'] = 'Starting ID (should be 100, 200, or such)'
        self.start_ID_label['wraplength'] = 250
        self.start_ID_label.pack(side='top', pady=5)
        self.start_ID = tk.Entry(self)
        self.start_ID.pack(side='top', pady=5)

        self.output_name_label = tk.Label(self)
        self.output_name_label['text'] = 'Output file names'
        self.output_name_label['wraplength'] = 170
        self.output_name_label.pack(side='top', pady=5)
        self.output_name = tk.Entry(self)
        self.output_name.pack(side='top', pady=5)

        self.party_loot_label = tk.Label(self)
        self.party_loot_label['text'] = 'Loot change per +/-'
        self.party_loot_label.pack(side='top', pady=0)
        self.party_loot = tk.Scale(self, from_=0, to=500, orient=tk.HORIZONTAL,
                              resolution=5,  command=self.update_positions, length=250)
        self.party_loot.set(PARTY_DEFAULT_DELTA['loot'])
        self.party_loot.pack(side='top', pady=0)

        self.party_morale_label = tk.Label(self)
        self.party_morale_label['text'] = 'Morale change per +/-'
        self.party_morale_label.pack(side='top', pady=0)
        self.party_morale = tk.Scale(self, from_=0, to=2.5, orient=tk.HORIZONTAL,
                              resolution=0.05,  command=self.update_positions, length=250)
        self.party_morale.set(PARTY_DEFAULT_DELTA['morale'])
        self.party_morale.pack(side='top', pady=0)

        self.party_manpower_label = tk.Label(self)
        self.party_manpower_label['text'] = 'Manpower change per +/-'
        self.party_manpower_label.pack(side='top', pady=0)
        self.party_manpower = tk.Scale(self, from_=0, to=500, orient=tk.HORIZONTAL,
                              resolution=5,  command=self.update_positions, length=250)
        self.party_manpower.set(PARTY_DEFAULT_DELTA['manpower'])
        self.party_manpower.pack(side='top', pady=0)

        self.party_supplies_label = tk.Label(self)
        self.party_supplies_label['text'] = 'Supply change per +/-'
        self.party_supplies_label.pack(side='top', pady=0)
        self.party_supplies = tk.Scale(self, from_=0, to=25, orient=tk.HORIZONTAL,
                              resolution=0.5,  command=self.update_positions, length=250)
        self.party_supplies.set(PARTY_DEFAULT_DELTA['supplies'])
        self.party_supplies.pack(side='top', pady=0)

        self.party_effectiveness_label = tk.Label(self)
        self.party_effectiveness_label['text'] = 'Effectiveness change per +/-'
        self.party_effectiveness_label.pack(side='top', pady=0)
        self.party_effectiveness = tk.Scale(self, from_=0, to=25, orient=tk.HORIZONTAL,
                              resolution=0.5,  command=self.update_positions, length=250)
        self.party_effectiveness.set(PARTY_DEFAULT_DELTA['effectiveness'])
        self.party_effectiveness.pack(side='top', pady=0)

        self.party_reset = tk.Button(self)
        self.party_reset['text'] = 'Reset to default values'
        self.party_reset['command'] = self.reset_positions
        self.party_reset.pack(side='top', pady=5)

        self.drawio_data_label = tk.Label(self)
        self.drawio_data_label['text'] = 'Uncompressed draw.io XML data\n(Copied from Extras -> Edit Diagram)'
        self.drawio_data_label.pack(side='top', pady=5)

        self.drawio_data = ScrolledText(self, width=50, height=15, wrap="word")
        self.drawio_data.pack(side='top', pady=5)

    def reset_positions(self):
        self.party_loot.set(PARTY_DEFAULT_DELTA['loot'])
        self.party_morale.set(PARTY_DEFAULT_DELTA['morale'])
        self.party_manpower.set(PARTY_DEFAULT_DELTA['manpower'])
        self.party_supplies.set(PARTY_DEFAULT_DELTA['supplies'])
        self.party_effectiveness.set(PARTY_DEFAULT_DELTA['effectiveness'])
        self.update_positions()        

    def update_positions(self, _=0):
        self.party_statistics_delta = {
            'loot': self.party_loot.get(),
            'morale': self.party_morale.get(),
            'manpower': self.party_manpower.get(),
            'supplies': self.party_supplies.get(), 
            'effectiveness': self.party_effectiveness.get() 
            }        

    def run_app(self):
        try:
            dungeon = Dungeon(self.dungeon_name.get(), self.drawio_data.get(1.0, tk.END), 
                              int(self.start_ID.get()), self.party_statistics_delta)
            print('Dungeon files generated.')
            os.makedirs("output", exist_ok=True)
            output_name = self.output_name.get().replace(' ','_')
            dungeon.write_to_file(f'output/{output_name}')
            self.output_text.set(
                f"{self.dungeon_name.get()} has been processed! Check the output folder.")

        except:
            self.output_text.set(
                "Something went wrong. Please consult Magnive.")
            
            
root = tk.Tk()
root.geometry('500x800')
root.title('Draw.io Converter')
app = App(master=root)
app.mainloop()
