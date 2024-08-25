import json
import math
import random
import re

# Load skills from JSON file
def load_skills(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Load party members from JSON file
def load_party_members(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        party_members = []
        for member in data['partyMembers']:
            member['max_hp'] = member['hp']
            member['max_sp'] = member['sp']
            member['is_down'] = False
            member['weaknesses'] = member['weak'].split(',') if member['weak'] else []
            member['strengths'] = member['strong'].split(',') if member['strong'] else []
            member['null'] = member['null'].split(',') if member['null'] else []
            member['reflect'] = member['reflect'].split(',') if member['reflect'] else []
            member['absorb'] = member['absorb'].split(',') if member['absorb'] else []
            party_members.append(member)
        return party_members
    
def load_shadows(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        shadows = []
        for shadow in data:
            processed_shadow = {
                'name': shadow['Name'],
                'strength': int(shadow['Strength']),
                'magic': int(shadow['Magic']),
                'endurance': int(shadow['Endurance']),
                'agility': int(shadow['Agility']),
                'luck': int(shadow['Luck']),
                'hp': int(shadow['Max HP']),
                'max_hp': int(shadow['Max HP']),
                'sp': int(shadow['Max SP']),
                'max_sp': int(shadow['Max SP']),
                'weaknesses': [],
                'strengths': [],
                'null': [],
                'reflect': [],
                'absorb': [],
                'is_down': False,
                'weapon': 0,
                'armor': 0
            }
            
            elements = ['Slash', 'Strike', 'Pierce', 'Fire', 'Ice', 'Elec', 'Wind', 'Light', 'Dark', 'Almighty']
            for element in elements:
                affinity = shadow[element].split()[0].lower()
                if affinity == 'weak':
                    processed_shadow['weaknesses'].append(element.lower())
                elif affinity == 'resist':
                    processed_shadow['strengths'].append(element.lower())
                elif affinity == 'null':
                    processed_shadow['null'].append(element.lower())
                elif affinity == 'reflect':
                    processed_shadow['reflect'].append(element.lower())
                elif affinity == 'absorb':
                    processed_shadow['absorb'].append(element.lower())
            
            shadows.append(processed_shadow)
        return shadows

# Calculate damage for party members
def calculate_damage_party(skill_power, offense, defense, level_difference, affinity):
    if skill_power == 0:
        return 0
    damage = math.sqrt(skill_power * 15 * offense / defense) * 2 * level_difference * affinity
    return int(damage)  # Round toward 0

# Calculate damage for shadows
def calculate_damage_shadow(skill_power, offense, defense, armor, level_difference, affinity, is_melee):
    if skill_power == 0:
        return 0
    damage = (math.sqrt(skill_power * 6 * offense / (8 * defense + armor)) * 9 * level_difference) * affinity
    if not is_melee:
        damage -= 10
    return int(damage)  # Round toward 0

def get_shadow_info(all_shadows):
    print("Enter information for shadows:")
    num_shadows = int(input("How many shadows do you want? "))
    shadows = []
    
    for i in range(num_shadows):
        while True:
            name = input(f"Enter the name of Shadow {i+1}: ").lower()
            shadow = next((s for s in all_shadows if s['name'].lower() == name), None)
            if shadow:
                shadows.append(shadow)
                break
            else:
                print(f"Shadow '{name}' not found. Please try again.")
    
    return shadows

# Find skill in the skills dictionary
def find_skill(skills, skill_name):
    for element, element_skills in skills.items():
        if skill_name in element_skills:
            return element, element_skills[skill_name]
    return None, None

# Calculate skill cost
def calculate_skill_cost(character, cost_type, cost_value):
    if isinstance(cost_value, str):
        cost_value = re.sub(r'[^\d%]', '', cost_value)
        
        if cost_value.endswith('%'):
            percentage = int(cost_value[:-1])
            if cost_type == 'hp':
                return int(character['max_hp'] * percentage / 100)
            elif cost_type == 'sp':
                return int(character['max_sp'] * percentage / 100)
        else:
            return int(cost_value)
    elif isinstance(cost_value, (int, float)):
        return int(cost_value)
    else:
        raise ValueError(f"Unsupported cost value type: {type(cost_value)}")

# Calculate crit chance for melee attacks
def calculate_crit_chance(attacker, defender, is_shadow):
    crit_chance = (attacker['luck'] + 50) / (defender['luck'] + 50) * 3
    if is_shadow:
        crit_chance *= 0.8
    return int(crit_chance)  # Round toward 0

# Calculate number of hits for multi-hit skills
def calculate_num_hits(num_hits_str):
    if num_hits_str.startswith("range:"):
        min_hits, max_hits = map(int, num_hits_str.split(":")[1].split("-"))
        base_hits = min_hits
        extra_hits = 0
        for _ in range(max_hits - min_hits):
            if random.random() < 1 / (max_hits - min_hits + 1):
                extra_hits += 1
            else:
                break
        return base_hits + extra_hits
    elif num_hits_str.startswith("single:"):
        return int(num_hits_str.split(":")[1])
    else:
        raise ValueError(f"Invalid num_hits format: {num_hits_str}")

# Use skill
def use_skill(attacker, defenders, skill_name, skill_data, skill_element, is_shadow, baton_pass_multiplier=1):
    skill_power = skill_data['skill_power']
    cost_type = skill_data['cost']['type']
    cost_value = skill_data['cost']['value']
    
    actual_cost = calculate_skill_cost(attacker, cost_type, cost_value)
    
    # Check if attacker has enough HP/SP to use the skill
    if cost_type == 'sp' and attacker['sp'] < actual_cost:
        print(f"Not enough SP to use {skill_name}!")
        return False, []
    elif cost_type == 'hp' and attacker['hp'] < actual_cost:
        print(f"Not enough HP to use {skill_name}!")
        return False, []
    
    # Deduct the cost
    if cost_type == 'sp':
        attacker['sp'] -= actual_cost
    else:  # HP cost
        attacker['hp'] -= actual_cost
    
    print(f"{attacker['name']} uses {skill_name}!")
    
    downed_targets = []
    critical_hit = False
    
    # Check for instant kill chance
    insta_kill_chance = int(skill_data.get('insta_chance', '0%').rstrip('%'))
    is_insta_kill = random.randint(1, 100) <= insta_kill_chance

    # Determine number of hits for multi-hit skills
    num_hits = 1
    if skill_data.get('multi_hit') == 'y':
        num_hits = calculate_num_hits(skill_data['num_hits'])
        print(f"Multi-hit skill: {num_hits} hits!")

    # Apply damage to target(s)
    for target in defenders:
        if target['hp'] <= 0:
            continue
        
        # Check for null, reflect, or absorb
        if skill_element in target['null']:
            print(f"{target['name']} nullified the {skill_element} attack!")
            continue
        elif skill_element in target['reflect']:
            print(f"{target['name']} reflected the {skill_element} attack!")
            reflected_damage = calculate_damage_party(skill_power, attacker['strength'] if skill_element in ['phys', 'gun'] else attacker['magic'], attacker['endurance'], 1, 1)
            attacker['hp'] -= reflected_damage
            print(f"{attacker['name']} took {reflected_damage} reflected damage!")
            continue
        elif skill_element in target['absorb']:
            absorbed_damage = calculate_damage_party(skill_power, attacker['strength'] if skill_element in ['phys', 'gun'] else attacker['magic'], target['endurance'], 1, 1)
            target['hp'] = min(target['max_hp'], target['hp'] + absorbed_damage)
            print(f"{target['name']} absorbed {absorbed_damage} HP from the {skill_element} attack!")
            continue

        # Handle instant kill skills
        if is_insta_kill:
            target['hp'] = 0
            print(f"Instant kill! {target['name']} is defeated!")
            target['is_down'] = True
            downed_targets.append(target)
            continue

        # Calculate and apply damage for each hit
        total_damage = 0
        for _ in range(num_hits):
            if is_shadow:
                damage = calculate_damage_shadow(
                    skill_power, 
                    attacker['strength'] if skill_element in ['phys', 'gun'] else attacker['magic'],
                    target['endurance'], 
                    target['armor'],
                    1,  # level difference
                    1.25 if skill_element in target['weaknesses'] else 0.5 if skill_element in target['strengths'] else 1,
                    skill_name == 'melee'
                )
            else:
                damage = calculate_damage_party(
                    skill_power if skill_name != 'melee' else attacker['weapon'] // 2,
                    attacker['strength'] if skill_element in ['phys', 'gun'] else attacker['magic'],
                    target['endurance'],
                    1,  # level difference
                    1.25 if skill_element in target['weaknesses'] else 0.5 if skill_element in target['strengths'] else 1
                )
            
            # Apply baton pass multiplier
            damage = int(damage * baton_pass_multiplier)
            
            # Check for critical hit
            if skill_name == 'melee':
                crit_chance = calculate_crit_chance(attacker, target, is_shadow)
                if random.randint(1, 100) <= crit_chance:
                    damage = int(damage * 1.5)
                    critical_hit = True
                    print(f"Critical hit! (Crit chance: {crit_chance}%)")
            elif 'crit_chance' in skill_data:
                crit_chance = int(re.sub(r'[^\d]', '', skill_data['crit_chance']))
                if random.randint(1, 100) <= crit_chance:
                    damage = int(damage * 1.5)
                    critical_hit = True
                    print("Critical hit!")
            
            total_damage += damage

        target['hp'] = max(0, target['hp'] - total_damage)
        
        if skill_element in target['weaknesses']:
            print(f"Weak! {target['name']} took {total_damage} damage.")
            target['is_down'] = True
            downed_targets.append(target)
        elif skill_element in target['strengths']:
            print(f"Resisted. {target['name']} took {total_damage} damage.")
        else:
            print(f"{target['name']} took {total_damage} damage.")
        
        print(f"{target['name']}'s remaining HP: {target['hp']}")
        
        if critical_hit:
            target['is_down'] = True
            downed_targets.append(target)
    
    return True, downed_targets

# Perform all-out attack
def all_out_attack(party, shadows):
    first_party_member = party[0]
    skill_power = first_party_member['weapon'] // 2
    
    for shadow in shadows:
        if shadow['hp'] <= 0:
            continue
        
        damage = int(math.sqrt(skill_power * 15 * first_party_member['strength'] / shadow['endurance']) * 1.6 * 1 * len(party))
        shadow['hp'] = max(0, shadow['hp'] - damage)
        print(f"{shadow['name']} took {damage} damage from the All-Out Attack!")
        print(f"{shadow['name']}'s remaining HP: {shadow['hp']}")

# Main function
def main():
    skills = load_skills('skills.json')
    party = load_party_members('party.json')
    all_shadows = load_shadows('shadows.json')
    shadows = get_shadow_info(all_shadows)
    
    advantage = input("Who has the advantage? (party/shadows/neutral): ").lower()
    
    all_characters = sorted(party + shadows, key=lambda x: x['agility'], reverse=True)
    
    if advantage == "party":
        all_characters = party + [c for c in all_characters if c not in party]
    elif advantage == "shadows":
        all_characters = shadows + [c for c in all_characters if c not in shadows]
    
    # Main game loop
    turn = 0
    while any(member['hp'] > 0 for member in party) and any(shadow['hp'] > 0 for shadow in shadows):
        turn += 1
        print(f"\n--- Turn {turn} ---")
        
        for character in all_characters:
            if character['hp'] <= 0:
                continue
            
            print(f"\n{character['name']}'s turn")
            print(f"HP: {character['hp']}/{character['max_hp']}, SP: {character['sp']}/{character['max_sp']}")
            
            is_shadow = character in shadows
            baton_pass_multiplier = 1
            
            while True:
                skill_name = input("Enter the name of the skill to use (or 'melee' for melee attack, 'skip' to skip turn): ").lower()
                if skill_name == 'skip':
                    print(f"{character['name']} skips their turn.")
                    break
                
                if skill_name == 'melee':
                    skill_element = 'phys'
                    skill_data = {
                        'skill_power': character['weapon'] // 2 if not is_shadow else 1,
                        'target_type': 'single-target',
                        'cost': {'type': 'hp', 'value': '0'}
                    }
                else:
                    skill_element, skill_data = find_skill(skills, skill_name)
                
                if skill_data is None:
                    print("Invalid skill name. Try again.")
                    continue
                
                if skill_data['target_type'] == 'single-target':
                    targets = shadows if character in party else party
                    print("Available targets:")
                    for i, target in enumerate(targets):
                        if target['hp'] > 0:
                            print(f"{i+1}. {target['name']} (HP: {target['hp']}/{target['max_hp']})")
                    
                    target_index = int(input("Enter the number of the target: ")) - 1
                    if 0 <= target_index < len(targets) and targets[target_index]['hp'] > 0:
                        success, downed = use_skill(character, [targets[target_index]], skill_name, skill_data, skill_element, is_shadow, baton_pass_multiplier)
                    else:
                        print("Invalid target. Try again.")
                        continue
                else:
                    targets = shadows if character in party else party
                    success, downed = use_skill(character, [t for t in targets if t['hp'] > 0], skill_name, skill_data, skill_element, is_shadow, baton_pass_multiplier)
                
                if success:
                    if downed and not is_shadow:
                        print("One More!")
                        if len(downed) == len([s for s in shadows if s['hp'] > 0]):
                            if input("All enemies are down! Perform an All-Out Attack? (y/n): ").lower() == 'y':
                                all_out_attack(party, shadows)
                                break
                        if input("Baton Pass? (y/n): ").lower() == 'y':
                            print("Available party members:")
                            available_members = [m for m in party if m['hp'] > 0 and m != character]
                            for i, member in enumerate(available_members):
                                print(f"{i+1}. {member['name']}")
                            member_index = int(input("Enter the number of the party member to pass to: ")) - 1
                            if 0 <= member_index < len(available_members):
                                character = available_members[member_index]
                                baton_pass_multiplier *= 1.25
                                print(f"Baton passed to {character['name']}! Attack multiplier: x{baton_pass_multiplier:.2f}")
                                continue
                    break
                else:
                    print("Failed to use skill. Try again.")
        
        # Reset downed status at the end of each round
        for character in all_characters:
            character['is_down'] = False
    
    # End of battle
    if any(member['hp'] > 0 for member in party):
        print("\nParty wins!")
    else:
        print("\nShadows win!")

if __name__ == "__main__":
    main()
