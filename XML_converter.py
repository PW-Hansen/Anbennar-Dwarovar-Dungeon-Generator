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
	id = diggy_dungeons.event_ID
	title = diggy_dungeons.event_ID.t
desc_placeholder
	picture = TRADEGOODS_eventPicture
	
	is_triggered_only = yes
	
	trigger = {
		has_province_flag = sent_expedition_@owner
	}
options_placeholder
}
'''

# Desc regular.
DESC_SINGLE = '\tdesc = diggy_dungeons.event_ID.d'

# Desc multiple.
DESC_MULTIPLE = '''\tdesc = {
		trigger = { always = yes }
		desc = diggy_dungeons.event_ID.d.1
	}
	desc = {
		trigger = { always = no }
		desc = diggy_dungeons.event_ID.d.2
	}
'''

# Base structure of an option.
OPTION_BASE = '''
	option = {
		name = diggy_dungeons.event_ID.option_ID
		ai_chance = { factor = 100 }
		trigger = {
			always = yes
		}
event_effects
	}'''

# Base structure of party statistics change.
PARTY_BASE_CHANGE_ADD = '\t\tchange_party_stat = { add_tooltip = yes add = value}\n'

# Party attributes and their default change values.
PARTY_DEFAULT_DELTA = { 
    'loot': 75,
    'morale': 0.5,
    'manpower': 200,
    'supplies': 4, 
    'effectiveness': 5    
}

# Changing a variable value
VARIABLE_CHANGE_BASE = '\t\tchange_variable = { which = variable_name value = value_change}\n'

# ADK effect
ADK_EFFECT = '\t\tadd_adk_effect = { add = value_change }'

# Dungeon progress.
PROGRESS_BASE = '\n\t\tdungeon_progress_advancement = { id = progress_ID }'

# Encounter effect.
ENCOUNTER_EFFECT_BASE = '''		
        dungeon_encounter_effect = {
			base_success = success_chance
			success_id = success_target
			
			base_failure = failure_chance
			failure_id = failure_target
		}'''

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
    id = diggy_dungeons.event_ID
    title = diggy_dungeons.event_ID.t
    desc = diggy_dungeons.event_ID.d
    picture = CAVE_eventPicture
    
    is_triggered_only = yes
    
    trigger = {
        always = yes
    }
    
    immediate = {
    }
    
    after = {
    }
    
    # Nice
    option = {
        name = diggy_dungeons.event_ID.a
        ai_chance = { factor = 100 }
    }
}
'''

# End event string.
END_EVENT_STRING = '''
    immediate = {
        dungeon_immediate_effect = yes
    }

    option = {
        name = diggy_dungeons.event_ID.a
        ai_chance = { factor = 100 }
        trigger = {
            always = yes
        }
        special_reward_expedition = yes
        currency_effect_expedition = {  currency = treasury cash = yes addTo = owner }
        currency_effect_expedition = {  currency = adm_power mana = yes addTo = owner }
        currency_effect_expedition = {  currency = dip_power mana = yes addTo = owner }
        currency_effect_expedition = {  currency = mil_power mana = yes addTo = owner }
        hidden_effect = {
            while = {
                limit = { check_variable = { partyManpower = 1000 } }
                subtract_variable = { partyManpower = 1000 }
                owner = { add_manpower = 1 }
            }
        }
        custom_tooltip = back_to_manpower_tooltip
        custom_tooltip = base_expedition_loot_tooltip
        if = {
            limit = { check_variable = { ancientDwarvenKnowledge = 1 } }
            province_event = { id = diggy_expedition.14 }
        }
        else = { hidden_effect = { clear_expedition_effect = yes } }
        hidden_effect = { set_province_flag = floor_explored }
    }
'''

# Localization structure.
LOCALIZATION_BASE = ' diggy_dungeons.event_ID.loc_ID:0 "Text"\n'


# Hex color identities.
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
        
        if not debug:
            self.get_elements()
            self.get_events()
            self.get_floors()
            self.error_check()
        
    def __repr__(self):
        return f'{type(self).__name__}: {self.name}'
    
    # Extracts the elements from the XML file.
    def get_elements(self):
        tree = ET.ElementTree(ET.fromstring(self.XML_string))
        root = tree.getroot()
        self.elements = [root[0][0][0][i] for i in range(len(root[0][0][0]))]
    
    # Extracts the events from the elements.
    def get_events(self):
        events_dict = {}
        events_components = {}
        
        # Loops through each element and picks out elements which is a group, 
        # in which case it established as an event object and saved in a 
        # dictionary, or is a child of an event, in which case it is added to
        # that event as a  component.
        # Furthermore, checks whether an element is an arrow. If so, establish
        # a connection between the target and the source.
        for element in self.elements:
            keys = element.keys()
            attribs = element.attrib
            if 'style' in keys:
                if 'group' in attribs['style']: # Not = 'group' due to some groups being rotated.
                    events_dict[attribs['id']] = Event(element, self)
                elif attribs['parent'] in events_dict:
                    events_dict[attribs['parent']].add_component(element)
                    events_components[attribs['id']] = events_dict[attribs['parent']]
        for element in self.elements:
            keys = element.keys()
            attribs = element.attrib
            if 'target' in keys:
                source_opt      = attribs['source']
                source_event    = events_components[source_opt]
                target          = events_components[attribs['target']]
                
                source_event.add_connection(source_opt,target)
    
        # Saves the events to the dungeon class.
        self.events = [v for k,v in events_dict.items()]
        
    # Splits the events into floors.
    def get_floors(self):
        self.floors = []
        self.level = 0
        self.event_IDs = self.ID_start

        for event in self.events:
            if not hasattr(event, 'event_ID'):
                self.top_event = event
                self.floor_set_top_event()
                self.floor_set_event_ID(debug = False)

    # Looks for incoming connections to an event. If there is at least one, go
    # to the first incoming connection and repeat the process.
    def floor_set_top_event(self):
        while len(self.top_event.connections_in) > 0:
            self.top_event = self.top_event.connections_in[0]

    # When supplies with a top event of a floor, assigns that event a
    # specified ID, then increments the ID, accesses the children of said
    # event, gives them ID, and adds their outgoing connections, and so on, 
    # until all events in a floor have been assigned an ID.
    # During this process, all events connected to the top event are saved in
    # a list for the floor object.
    def floor_set_event_ID(self, debug = False):
        floor_events = [self.top_event]
        for event in floor_events:
            self.event_IDs += 1
            event.event_ID = self.event_IDs
            for connection_out in event.connections_out:
                if not hasattr(connection_out, 'event_ID'):
                    connection_out.event_ID = self.event_IDs
                    floor_events.append(connection_out)
            
        if debug:
            print(floor_events)                
        
        if len(floor_events) > 0:
            self.level += 1
            self.floors.append(Floor(self,self.level,floor_events))    

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
        with open(f'{file_name}.txt', 'a') as file:
            file.write(f'Dungeon: {self.name}\n')            
            file.write(START_EVENT_STRING.replace('event_ID', str(self.ID_start)))
            for floor in self.floors:
                file.write(f'# {str(floor)}')
                for event in floor.events:
                    event.write_event(file)
        with open(f'{file_name}.yml', 'a') as file:
            file.write('l_english:\n')
            file.write(f' diggy_dungeons.{self.ID_start}.t:0 ""\n')
            file.write(f' diggy_dungeons.{self.ID_start}.d:0 ""\n')
            file.write(f' diggy_dungeons.{self.ID_start}.a:0 ""\n')
            file.write('\n')
            for floor in self.floors:
                for event in floor.events:
                    for component in event.components:
                        component.write_loc(file)
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
    def __init__(self, xml_element, dungeon):
        self.xml_element = xml_element
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
        
    def add_component(self,xml_element):
        if self.title == None:
            self.title = Title(xml_element, self)
        elif self.desc == None:
            self.desc = Desc(xml_element, self)
        else:
            self.options.append(Option(xml_element, self))

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
    def __init__(self, xml_element, parent):
        self.xml_element = xml_element
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
            self.difficulty = self.text.split('(')[1].strip(')')
            if self.difficulty in SUCCESS_CHANCE:
                self.base_succes = SUCCESS_CHANCE[self.difficulty]
            else:
                self.base_succes = int(self.difficulty)
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
        
        # Encounter effect for when an option has a success outcome.
        if hasattr(self,'success'):
            # Check if there is a success event but no failure event. If so, try to find another
            # event outcome, and assign that as the failure event.
            if not hasattr(self,'failure'):
                for event in self.outcomes:
                    if event.type != 'Success':
                        self.failure = event

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
