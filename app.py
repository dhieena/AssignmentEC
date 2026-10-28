import streamlit as st
import pandas as pd
import random
import csv
import os

# Set up page layout
st.set_page_config(
    page_title="TV Program Schedule Optimizer",
    layout="wide"
)

st.title("📺 TV Program Schedule Optimizer")

# Internal Fixed GA Parameters (Hidden from UI)
GEN = 100
POP = 50
EL_S = 2

# READ CSV DATA
def read_csv_to_dict(file_path):
    program_ratings = {}
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header
        for row in reader:
            if not row:
                continue
            program = row[0]
            ratings = [float(x) for x in row[1:]]
            program_ratings[program] = ratings
    return program_ratings

# Look for modified CSV first; fall back to original if not found
csv_filename = "program_ratings_modified.csv" if os.path.exists("program_ratings_modified.csv") else "program_ratings.csv"

if not os.path.exists(csv_filename):
    st.error(f"CSV file '{csv_filename}' not found. Please ensure 'program_ratings.csv' or 'program_ratings_modified.csv' is uploaded to your repository.")
    st.stop()

# Load dataset dictionary
ratings = read_csv_to_dict(csv_filename)
all_programs = list(ratings.keys())
num_slots = len(next(iter(ratings.values())))
all_time_slots = list(range(6, 6 + num_slots)) 

st.markdown("---")

# Display loaded ratings data
st.subheader("Loaded Program Ratings Data")
ratings_df = pd.DataFrame.from_dict(ratings, orient='index', columns=[f"Slot {s:02d}:00" for s in all_time_slots])
st.dataframe(ratings_df, use_container_width=True)

# GENETIC ALGORITHM LOGIC
def fitness_function(schedule):
    total_rating = 0
    for time_slot, program in enumerate(schedule):
        total_rating += ratings[program][time_slot]
    return total_rating

def crossover(schedule1, schedule2):
    if len(schedule1) <= 2:
        return schedule1.copy(), schedule2.copy()
    crossover_point = random.randint(1, len(schedule1) - 2)
    child1 = schedule1[:crossover_point] + schedule2[crossover_point:]
    child2 = schedule2[:crossover_point] + schedule1[crossover_point:]
    return child1, child2

def mutate(schedule):
    schedule_copy = schedule.copy()
    mutation_point = random.randint(0, len(schedule_copy) - 1)
    new_program = random.choice(all_programs)
    schedule_copy[mutation_point] = new_program
    return schedule_copy

def genetic_algorithm(initial_schedule, generations=GEN, population_size=POP, crossover_rate=0.8, mutation_rate=0.02, elitism_size=EL_S):
    population = [initial_schedule]

    for _ in range(population_size - 1):
        random_schedule = initial_schedule.copy()
        random.shuffle(random_schedule)
        population.append(random_schedule)

    best_fitness_history = []

    for generation in range(generations):
        # Sort population by fitness (Elitism)
        population.sort(key=lambda schedule: fitness_function(schedule), reverse=True)
        best_fitness_history.append(fitness_function(population[0]))
        
        new_population = []
        new_population.extend(population[:elitism_size])

        while len(new_population) < population_size:
            parent1, parent2 = random.choices(population, k=2)
            if random.random() < crossover_rate:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            if random.random() < mutation_rate:
                child1 = mutate(child1)
            if random.random() < mutation_rate:
                child2 = mutate(child2)

            new_population.extend([child1, child2])

        population = new_population[:population_size]

    population.sort(key=lambda schedule: fitness_function(schedule), reverse=True)
    return population[0], fitness_function(population[0]), best_fitness_history

# Initial schedule preparation
initial_schedule = all_programs.copy()
if len(initial_schedule) < len(all_time_slots):
    initial_schedule += random.choices(all_programs, k=len(all_time_slots) - len(initial_schedule))
else:
    initial_schedule = initial_schedule[:len(all_time_slots)]

# PARAMETER INPUTS 
st.markdown("---")
st.subheader("⚙️ Genetic Algorithm Parameters")

# Display sliders side-by-side in two columns on the main page
param_col1, param_col2 = st.columns(2)

with param_col1:
    co_r = st.slider(
        "Crossover Rate (CO_R)", 
        min_value=0.00, 
        max_value=0.95, 
        value=0.80, 
        step=0.05,
        help="Range: 0.0 to 0.95 (Default: 0.80)"
    )

with param_col2:
    mut_r = st.slider(
        "Mutation Rate (MUT_R)", 
        min_value=0.01, 
        max_value=0.05, 
        value=0.02, 
        step=0.01,
        help="Range: 0.01 to 0.05 (Default: 0.02)"
    )

# RUN TRIALS & DISPLAY TABLES
if 'trials' not in st.session_state:
    st.session_state.trials = []

st.markdown("---")
st.subheader("Run Experimental Trials")

col1, col2 = st.columns([1, 4])
with col1:
    run_btn = st.button("🚀 Run GA Trial", type="primary")
with col2:
    if st.button("🗑️ Clear Trials"):
        st.session_state.trials = []
        st.rerun()

if run_btn:
    if len(st.session_state.trials) >= 3:
        st.warning("You have already recorded 3 trials! Click 'Clear Trials' to restart.")
    else:
        best_sched, total_score, history = genetic_algorithm(
            initial_schedule=initial_schedule,
            generations=GEN,
            population_size=POP,
            crossover_rate=co_r,
            mutation_rate=mut_r,
            elitism_size=EL_S
        )
        
        # Build schedule output table
        table_rows = []
        for time_slot_idx, program in enumerate(best_sched):
            time_str = f"Slot {all_time_slots[time_slot_idx]:02d}:00 - {all_time_slots[time_slot_idx]+1:02d}:00"
            rating_val = ratings[program][time_slot_idx]
            table_rows.append({
                "Time Slot": time_str,
                "Scheduled Program": program,
                "Assigned Rating": rating_val
            })
        
        schedule_table = pd.DataFrame(table_rows)
        trial_number = len(st.session_state.trials) + 1
        
        st.session_state.trials.append({
            "Trial": f"Trial {trial_number}",
            "CO_R": co_r,
            "MUT_R": mut_r,
            "Total Ratings Score": round(total_score, 2),
            "Schedule Table": schedule_table,
            "History": history
        })
        
    st.subheader("Generated Schedule Tables")
    tabs = st.tabs([t["Trial"] for t in st.session_state.trials])
    
    for tab, t in zip(tabs, st.session_state.trials):
        with tab:
            st.markdown(f"**Parameters:** `CO_R` = {t['CO_R']} | `MUT_R` = {t['MUT_R']}")
            st.markdown(f"**Total Ratings Score:** `{t['Total Ratings Score']}`")
            st.dataframe(t["Schedule Table"], use_container_width=True)
            st.line_chart(t["History"], height=180)

# Display recorded trial summary and output tables
if st.session_state.trials:
    st.subheader("Experimental Trials Summary")
    
    summary_list = [{
        "Trial": t["Trial"],
        "Crossover Rate (CO_R)": t["CO_R"],
        "Mutation Rate (MUT_R)": t["MUT_R"],
        "Total Ratings Score": t["Total Ratings Score"]
    } for t in st.session_state.trials]
    
    st.table(pd.DataFrame(summary_list))

