import json
import math
import re

# Load skills from JSON file
def load_skills(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Calculate damage
def calculate_damage(skill_power, offense, defense, level_difference, affinity):
    damage = math.sqrt(skill_power * 15 * offense / defense) * 2 * level_difference * affinity
    return int(damage)  # Round toward 0

# Get user input for characters
def get_character_info(character_type):
    print(f"Enter information for {character_type}:")
    num_characters = int(input(f"How many {character_type} do you want? "))
    characters = []
    
    for i in range(num_characters):
        print(f"{character_type.capitalize()} {i+1}:")
        strength = int(input("Strength: "))
        magic = int(input("Magic: "))
        endurance = int(input("Endurance: "))
        hp = int(input("HP: "))
        sp = int(input("SP: "))
        
        weaknesses = input("Enter elements they're weak to (comma-separated): ").split(',')
        strengths = input("Enter elements they're strong to (comma-separated): ").split(',')
        
        characters.append({
            'name': f"{character_type.capitalize()} {i+1}",
            'strength': strength,
            'magic': magic,
            'endurance': endurance,
            'hp': hp,
            'max_hp': hp,
            'sp': sp,
            'max_sp': sp,
            'weaknesses': [e.strip() for e in weaknesses],
            'strengths': [e.strip() for e in strengths]
        })
    
    return characters

# Find skill in the skills dictionary
def find_skill(skills, skill_name):
    for element, element_skills in skills.items():
        if skill_name in element_skills:
            return element, element_skills[skill_name]
    return None, None

# Calculate skill cost
def calculate_skill_cost(character, cost_type, cost_value):
    if isinstance(cost_value, str):
        # Remove any non-numeric characters except for the percentage sign
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

# Use skill
def use_skill(attacker, defenders, skill_name, skill_data, skill_element):
    skill_power = skill_data['skill_power']
    cost_type = skill_data['cost']['type']
    cost_value = skill_data['cost']['value']
    
    actual_cost = calculate_skill_cost(attacker, cost_type, cost_value)
    
    # Check if attacker has enough HP/SP to use the skill
    if cost_type == 'sp' and attacker['sp'] < actual_cost:
        print(f"Not enough SP to use {skill_name}!")
        return False
    elif cost_type == 'hp' and attacker['hp'] < actual_cost:
        print(f"Not enough HP to use {skill_name}!")
        return False
    
    # Deduct the cost
    if cost_type == 'sp':
        attacker['sp'] -= actual_cost
    else:  # HP cost
        attacker['hp'] -= actual_cost
    
    # Apply damage to target(s)
    if skill_data['target_type'] == 'single-target':
        target = defenders[0]  # Assuming the first defender is the chosen target
        apply_damage(attacker, target, skill_element, skill_power)
    else:  # multi-target
        for target in defenders:
            apply_damage(attacker, target, skill_element, skill_power)
    
    return True

# Apply damage to a target
def apply_damage(attacker, target, skill_element, skill_power):
    offense = attacker['magic'] if skill_element not in ['phys', 'gun'] else attacker['strength']
    defense = target['endurance']
    level_difference = 1  # As specified
    
    if skill_element in target['weaknesses']:
        affinity = 1.25
    elif skill_element in target['strengths']:
        affinity = 0.5
    else:
        affinity = 1
    
    damage = calculate_damage(skill_power, offense, defense, level_difference, affinity)
    target['hp'] = max(0, target['hp'] - damage)
    print(f"{target['name']} took {damage} damage. Remaining HP: {target['hp']}")

# Main function
def main():
    skills = load_skills('skills.json')
    
    party = get_character_info("party members")
    shadows = get_character_info("shadows")
    
    all_characters = party + shadows
    
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
            
            skill_name = input("Enter the name of the skill to use (or 'skip' to skip turn): ").lower()
            if skill_name == 'skip':
                print(f"{character['name']} skips their turn.")
                continue
            
            skill_element, skill_data = find_skill(skills, skill_name)
            
            if skill_data is None:
                print("Invalid skill name. Skipping turn.")
                continue
            
            if skill_data['target_type'] == 'single-target':
                if character in party:
                    targets = shadows
                else:
                    targets = party
                
                print("Available targets:")
                for i, target in enumerate(targets):
                    if target['hp'] > 0:
                        print(f"{i+1}. {target['name']} (HP: {target['hp']}/{target['max_hp']})")
                
                target_index = int(input("Enter the number of the target: ")) - 1
                if 0 <= target_index < len(targets) and targets[target_index]['hp'] > 0:
                    use_skill(character, [targets[target_index]], skill_name, skill_data, skill_element)
                else:
                    print("Invalid target. Skipping turn.")
            else:
                if character in party:
                    use_skill(character, [shadow for shadow in shadows if shadow['hp'] > 0], skill_name, skill_data, skill_element)
                else:
                    use_skill(character, [member for member in party if member['hp'] > 0], skill_name, skill_data, skill_element)
    
    # End of battle
    if any(member['hp'] > 0 for member in party):
        print("\nParty wins!")
    else:
        print("\nShadows win!")

if __name__ == "__main__":
    main()