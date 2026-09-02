import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Distribution of contracts across all 1640 clients
# Data from the analysis
distribution = {
    "1 contrato": 1081,
    "2 contratos": 268,
    "3 contratos": 137,
    "4 contratos": 73,
    "5 contratos": 35,
    "6 contratos": 14,
    "7 contratos": 3,
    "8 contratos": 5,
    "9 contratos": 2,
    "10+ contratos": 2,
}

categories = list(distribution.keys())
values = list(distribution.values())
colors_bar = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(categories)))[::-1]

# ---- CHART 1: Bar chart of distribution ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Bar chart
bars = ax1.bar(categories, values, color=colors_bar, edgecolor='white', linewidth=0.8, width=0.6)
for bar, val in zip(bars, values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 8, 
             str(val), ha='center', va='bottom', fontweight='bold', fontsize=11)

ax1.set_title('Distribucion de Contratos por Cliente', fontsize=14, fontweight='bold', pad=15)
ax1.set_xlabel('Cantidad de Contratos', fontsize=12)
ax1.set_ylabel('Numero de Clientes', fontsize=12)
ax1.set_facecolor('#f8f9fa')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.tick_params(axis='x', rotation=25)

# Pie chart (top 7 + "Otros")
labels_pie = list(distribution.keys())[:7] + ["Otros (10+)"]
sizes_pie = list(distribution.values())[:7] + [distribution.get("10+ contratos", 0)]
colors_pie = plt.cm.Set3(np.linspace(0, 1, len(labels_pie)))
explode = [0.05 if v > 200 else 0 for v in sizes_pie]

wedges, texts, autotexts = ax2.pie(sizes_pie, labels=None, autopct='%1.1f%%',
                                     colors=colors_pie, explode=explode,
                                     startangle=90, pctdistance=0.75,
                                     textprops={'fontsize': 9})
ax2.legend(wedges, [f"{l} ({s})" for l, s in zip(labels_pie, sizes_pie)],
           title="Contratos por Cliente", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
           fontsize=9)
ax2.set_title('Distribucion Porcentual', fontsize=14, fontweight='bold', pad=15)

plt.tight_layout()
output_path = r'C:\Users\yarleyc\Documents\New OpenCode Project\distribucion_contratos.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Distribution chart saved to: {output_path}")