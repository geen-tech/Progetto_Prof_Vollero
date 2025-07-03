import json
import matplotlib.pyplot as plt

# Carica i risultati dal file JSON
with open("results_full.json") as f:
    results_full = json.load(f)

with open("results_consistent.json") as f:
    results_consistent = json.load(f)

# Operazioni da plottare
operations = ['Write', 'Read', 'Fail', 'Recover']
full = [results_full[op] for op in operations]
consistent = [results_consistent[op] for op in operations]

x = range(len(operations))
width = 0.35

fig, ax = plt.subplots()
ax.bar([i - width/2 for i in x], full, width, label='Full')
ax.bar([i + width/2 for i in x], consistent, width, label='Consistent')

ax.set_xticks(x)
ax.set_xticklabels(operations)
ax.set_ylabel('Time (seconds)')
ax.set_title('Performance Comparison')
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()
