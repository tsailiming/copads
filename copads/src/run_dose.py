from datetime import datetime
import ragaraja as N
import register_machine as r
from dose_entities import Population, World
from dose_parameters import *

# Set Ragaraja instruction version
if ragaraja_version == 1: 
    ragaraja_instructions = N.ragaraja_v1
for instruction in N.ragaraja:
    if instruction not in ragaraja_instructions:
        N.ragaraja[instruction] = N.not_used

# Write DOSE parameters into result files
for name in population_names:
    f = open(result_files[name] + '.result.txt', 'a')
    f.write('STARTING SIMULATION - ' + str(datetime.utcnow()) + '\n')
    f.write('DOSE parameters:' + '\n')
    f.write('chromosome_size = ' + str(chromosome_size) + '\n')
    f.write('cytoplasm_size = ' + str(cytoplasm_size) + '\n')
    f.write('population_size = ' + str(population_size) + '\n')
    f.write('population_names = ' + str(population_names) + '\n')
    f.write('world_x = ' + str(world_x) + '\n')
    f.write('world_y = ' + str(world_y) + '\n')
    f.write('world_z = ' + str(world_z) + '\n')
    f.write('population_locations = ' + str(population_locations) + '\n')
    f.write('background_mutation_rate = ' + str(background_mutation_rate) + '\n')
    f.write('additional_mutation_rate = ' + str(additional_mutation_rate) + '\n')
    f.write('maximum_generations = ' + str(maximum_generations) + '\n')
    f.write('fossilized_ratio = ' + str(fossilized_ratio) + '\n')
    f.write('fossilized_frequency = ' + str(fossilized_frequency) + '\n')
    f.write('fossil_files = ' + str(fossil_files) + '\n')
    f.write('print_frequency = ' + str(print_frequency) + '\n')
    f.write('result_files = ' + str(result_files) + '\n')
    f.write('ragaraja_version = ' + str(ragaraja_version) + '\n')
    f.write('instruction_set = ' + str(ragaraja_instructions) + '\n')
    f.close()
    
populations = {}
world = World()

for i in range(len(population_names)): 
    populations[population_names[i]] = Population()
    L = population_locations[i]
    world.ecosystem[L[0]][L[1]][L[2]]['organisms'] = \
        len(populations[population_names[i]].agents)
    for x in range(len(populations[population_names[i]].agents)):
        populations[population_names[i]].agents[x].status['location'] = L

########################################################################
# Default Simulation Driver                                            #
# (do not change anything above this line)                             #
########################################################################
generation_count = 0
while generation_count < maximum_generations:
    generation_count = generation_count + 1
    '''
    Run World.ecoregulate function
    '''
    world.ecoregulate()
    
    '''
    For each ecological cell, run World.update_ecology and 
    World.update_local functions
    '''
    for x in range(world.world_x):
        for y in range(world.world_y):
            for z in range(world.world_z):
                world.update_ecology(x, y, z)
                world.update_local(x, y, z)  
                
    '''
    For each organism
        Execute genome by Ragaraja interpreter using 
           existing cytoplasm, local conditions as input
        Update cytoplasm (Organism.cytoplasm)
        Add input/output from organism intermediate condition of local cell
    '''
    population_names = populations.keys()
    for name in population_names:
        for i in range(len(populations[name].agents)):
            source = populations[name].agents[i].genome.sequence
            array = populations[name].agents[i].cytoplasm
            L = populations[name].agents[i].status['location']
            inputdata = world.ecosystem[L[0]][L[1]][L[2]]['local_input']
            (array, apointer, inputdata, output, source, spointer) = \
                r.interpret(source, N.ragaraja, 3, inputdata, array, 10)
            populations[name].agents[i].genome.sequence = source
            populations[name].agents[i].cytoplasm = array
            world.ecosystem[L[0]][L[1]][L[2]]['temporary_input'] = inputdata
            world.ecosystem[L[0]][L[1]][L[2]]['temporary_output'] = output
    
    '''        
    For each population
        Run Population.prepopulation_control function
        Run Population.mating function and add new organisms to cell
        For each organism, run Organism.mutation_scheme function
        Run Population.generation_events function
        Add 1 to generation count
        Run Population.report function
        Fossilize population if needed
    '''
    for name in population_names:
        report = populations[name].generation_step()
        if generation_count % int(fossilized_frequency) == 0:
            ffile = fossil_files[name] + '_'
            populations[name].freeze(ffile, fossilized_ratio)
            
    '''
    For each ecological cell
        Run World.organism_movement function
       Run World.organism_location function
    '''
    for x in range(world.world_x):
        for y in range(world.world_y):
            for z in range(world.world_z):
                world.organism_movement(x, y, z)
                world.organism_location(x, y, z)
    
    '''
    Administrative tasks
    '''
    if generation_count % int(print_frequency) == 0:
        print str(generation_count), str(report)
        for name in population_names:
            f = open(result_files[name] + '.result.txt', 'a')
            dtstamp = str(datetime.utcnow())
            f.write('\t'.join([dtstamp, str(generation_count),
                               str(report)]))
            f.write('\n')
            f.close()