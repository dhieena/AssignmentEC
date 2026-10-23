import streamlit as st
import pandas as pd
import numpy as np
import random
import os

st.set_page_config(
    page_title="TV Scheduling GA Optimizer",
    layout="wide"
)

# ---------------------------------------------------------
# 1. LOAD & MODIFY CSV DATA
# ---------------------------------------------------------
@st.cache_data
def load_csv_data(filepath="program_ratings.csv"):
    """
    Loads original ratings CSV file.
    Falls back to dummy data if file is not found.
    """
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
    else:
        # Fallback dataset matching typical structure
        df = pd.DataFrame({
            'Program': ['News', 'Morning Show', 'Drama', 'Cartoons', 'Documentary', 'Movie', 'Sports', 'Talk Show'],
            'Rating': [3.5, 4.0, 6.0, 4.5, 5.0, 8.5, 9.0, 5.5]
        })
    return df

def apply_rating_modifications(df, adjustment_factor):
    """
    Applies custom modifications/assumptions to program ratings.
    """
    modified_df = df.copy()
    
    # Identify rating column name
    rating_col = [c for c in modified_df.columns if 'rating' in c.lower() or 'score' in c.lower()]
    target_col = rating_col[0] if rating_col else modified_df.columns[1]
    
    # Assumption: Apply scalar boost/adjustment to prime candidates
    modified_df['Modified_Rating'] = (modified_df[target_col] * adjustment_factor).round(2)
    return modified_df, target_col

# ---------------------------------------------------------
# 2. GENETIC ALGORITHM FOR SCHEDULING
# ---------------------------------------------------------
def calculate_fitness(chromosome, programs_df):
    total_score = 0.0
    seen = set()
    duplicates = 0
    
    # Example slot multipliers across standard broadcast hours
    slot_multipliers = [0.8, 0.9, 1.0, 1.1, 1.3, 1.7, 1.9, 1.2]
    
    for i, prog_idx in enumerate(chromosome):
        if prog_idx in seen:
            duplicates += 1
        seen.add(prog_idx)
        
        rating = programs_df.iloc[prog_idx]['Modified_Rating']
        multiplier = slot_multipliers[i] if i < len(slot_multipliers) else 1.0
        total_score += rating * multiplier
        
    # Penalty for duplicate assignments
    fitness = total_score - (duplicates * 15.0)
    return max(fitness, 0.0)

def create_population(pop_size, num_programs):
    population = []
    for _ in range(pop_size):
        ind = list(range(num_programs))
        random.shuffle(ind)
        population.append(ind)
    return population

def crossover(parent1, parent2, co_rate):
    if random.random() > co_rate:
        return parent1.copy(), parent2.copy()
    
    size = len(parent1)
    cx1, cx2 = sorted(random.sample(range(size), 2))
    
    def order_crossover(p1, p2):
        child = [-1] * size
        child[cx1:cx2] = p1[cx1:cx2]
        p2_idx = 0
        for i in range(size):
            if child[i] == -1:
                while p2[p2_idx] in child:
                    p2_idx += 1
                child[i] = p2[p2_idx]
        return child

    return order_crossover(parent1, parent2), order_crossover(parent2, parent1)

def mutate(individual, mut_rate):
    ind = individual.copy()
    for i in range(len(ind)):
        if random.random() < mut_rate:
            j = random.randint(0, len(ind) - 1)
            ind[i], ind[j] = ind[j], ind[i]
    return ind

def run_genetic_algorithm(programs_df, co_rate, mut_rate, pop_size=40, generations=80):
    num_programs = len(programs_df)
    population = create_population(pop_size, num_programs)
    best_history = []
    
    for _ in range(generations):
        fitness_scores = [calculate_fitness(ind, programs_df) for ind in population]
        best_history.append(max(fitness_scores))
        
        # Tournament selection
        selected = []
        for _ in range(pop_size):
            i1, i2 = random.sample(range(pop_size), 2)
            winner = population[i1] if fitness_scores[i1] > fitness_scores[i2] else population[i2]
            selected.append(winner.copy())
            
        # Reproduction
        next_gen = []
        for i in range(0, pop_size, 2):
            p1, p2 = selected[i], selected[i+1]
            c1, c2 = crossover(p1, p2, co_rate)
            c1 = mutate(c1, mut_rate)
            c2 = mutate(c2, mut_rate)
            next_gen.extend([c1, c2])
            
        population = next_gen

    final_scores = [calculate_fitness(ind, programs_df) for ind in population]
    best_idx = np.argmax(final_scores)
    return population[best_idx], final_scores[best_idx], best_history

# ---------------------------------------------------------
# 3. STREAMLIT INTERFACE
# ---------------------------------------------------------
st.title("📺 TV Program Schedule Optimizer")
st.caption("Individual Assignment — Genetic Algorithm Implementation")

# Sidebar - Requirements 3 Controls
st.sidebar.header("🕹️ Algorithm Parameters")

co_r = st.sidebar.slider(
    "Crossover Rate (CO_R)", 
    min_value=0.00, 
    max_value=0.95, 
    value=0.80, 
    step=0.05,
    help="Range: 0.0 to 0.95 (Default: 0.80)"
)

mut_r = st.sidebar.slider(
    "Mutation Rate (MUT_R)", 
    min_value=0.01, 
    max_value=0.05, 
    value=0.02, 
    step=0.01,
    help="Range: 0.01 to 0.05 (Default: 0.02)"
)

st.sidebar.markdown("---")
st.sidebar.header("📊 Rating Adjustment")
rating_mult = st.sidebar.slider("Rating Modifier Multiplier", 0.5, 2.0, 1.2, 0.1)

# Data Display
raw_data = load_csv_data("program_ratings.csv")[cite: 1]
modified_data, orig_col = apply_rating_modifications(raw_data, rating_mult)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Original CSV Data")[cite: 1]
    st.dataframe(raw_data, use_container_width=True)

with col2:
    st.subheader("Modified Ratings Data")
    st.dataframe(modified_data, use_container_width=True)

st.markdown("---")

# Session state to log the 3 required trials
if 'trials_log' not in st.session_state:
    st.session_state.trials_log = []

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    run_sim = st.button("▶️ Run Trial", type="primary")
with col_btn2:
    if st.button("🔄 Reset Trials"):
        st.session_state.trials_log = []
        st.rerun()

if run_sim:
    best_chrom, max_fit, history = run_genetic_algorithm(modified_data, co_r, mut_r)
    
    time_slots = [f"Slot {i+1} ({8+i*2:02d}:00 - {10+i*2:02d}:00)" for i in range(len(best_chrom))]
    prog_col = [c for c in modified_data.columns if 'prog' in c.lower() or 'name' in c.lower()]
    prog_name_col = prog_col[0] if prog_col else modified_data.columns[0]
    
    scheduled_names = [modified_data.iloc[idx][prog_name_col] for idx in best_chrom]
    scheduled_ratings = [modified_data.iloc[idx]['Modified_Rating'] for idx in best_chrom]
    
    res_table = pd.DataFrame({
        'Time Slot': time_slots[:len(best_chrom)],
        'Scheduled Program': scheduled_names,
        'Assigned Rating': scheduled_ratings
    })
    
    trial_count = len(st.session_state.trials_log) + 1
    st.session_state.trials_log.append({
        'Trial': f"Trial {trial_count}",
        'CO_R': co_r,
        'MUT_R': mut_r,
        'Fitness Score': round(max_fit, 2),
        'Schedule': res_table,
        'History': history
    })

# ---------------------------------------------------------
# 4. DISPLAY TRIALS & COMPARISON TABLE
# ---------------------------------------------------------
if st.session_state.trials_log:
    st.subheader("📋 Experimental Trials Summary")
    
    summary_df = pd.DataFrame([
        {
            'Trial': t['Trial'],
            'Crossover Rate (CO_R)': t['CO_R'],
            'Mutation Rate (MUT_R)': t['MUT_R'],
            'Best Fitness Score': t['Fitness Score']
        } for t in st.session_state.trials_log
    ])
    st.table(summary_df)

    st.subheader("📅 Trial Schedules")
    tabs = st.tabs([t['Trial'] for t in st.session_state.trials_log])
    
    for tab, t in zip(tabs, st.session_state.trials_log):
        with tab:
            st.markdown(f"**Parameters:** `CO_R` = {t['CO_R']} | `MUT_R` = {t['MUT_R']}")
            st.markdown(f"**Fitness Score:** `{t['Fitness Score']}`")
            st.dataframe(t['Schedule'], use_container_width=True)
            st.line_chart(t['History'], height=180)
