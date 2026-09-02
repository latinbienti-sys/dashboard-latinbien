import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Data from the analysis (Top 20 clients by contract count)
data = [
    ("FELIX EDEL LIMA DE LA SOTA", 19),
    ("GERARDO JOSE RAMIREZ F.", 14),
    ("SORELIS DEL CARMEN MORAN B.", 10),
    ("JOSE GREGORIO VILLASMIL G.", 9),
    ("YAHVEH ELIANGE MARQUEZ C.", 9),
    ("MA. CLAUDIA DEL R. PEREZ P.", 8),
    ("RUBISELA DEL VALLE MOYA G.", 8),
    ("EVELYN YEANINE QUINTERO U.", 8),
    ("DANIEL J. RODRIGUEZ V.", 8),
    ("YONATHAN JOSE VIVAS CARRERO", 8),
    ("JOHAN ANTONIO MONTES P.", 7),
    ("ROSMILA C. VALLADARES L.", 7),
    ("JAIRLEY N. DEL C. AMAYA M.", 7),
    ("OMAR ABRAHAM SALCEDO", 6),
    ("KARINA MOLINA VEGA", 6),
    ("FRANK A. VELASQUEZ H.", 6),
    ("LUIS EDUARDO UZCATEGUI", 6),
    ("CORY ESTEFANNY REINOZA M.", 6),
    ("LADY DIANA TORO RIVERA", 6),
    ("ALEXANDER J. GUTIERREZ V.", 6),
]

names = [d[0] for d in data]
values = [d[1] for d in data]

# Create the chart
fig, ax = plt.subplots(figsize=(14, 10))

# Colors - gradient Honda style (reds)
colors = plt.cm.Reds(np.linspace(0.3, 0.85, len(data)))[::-1]

bars = ax.barh(range(len(data)), values, color=colors, height=0.7, edgecolor='white', linewidth=0.5)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, values)):
    ax.text(val + 0.3, bar.get_y() + bar.get_height()/2, 
            str(int(val)), ha='left', va='center', 
            fontweight='bold', fontsize=11, color='#2c3e50')

# Customize
ax.set_yticks(range(len(data)))
ax.set_yticklabels(names, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel('Total de Contratos', fontsize=13, fontweight='bold', color='#2c3e50')
ax.set_title('TOP 20 CLIENTES CON MAS CONTRATOS\nHonda Merida - Analisis de Cartera', 
             fontsize=16, fontweight='bold', color='#1a1a2e', pad=20)

# Grid
ax.xaxis.grid(True, alpha=0.3, linestyle='--')
ax.set_axisbelow(True)
ax.set_xlim(0, max(values) + 4)

# Remove top/right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')

# Background color
ax.set_facecolor('#f8f9fa')
fig.patch.set_facecolor('#ffffff')

plt.tight_layout()
output_path = r'C:\Users\yarleyc\Documents\New OpenCode Project\top20_contratos_clientes.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Chart saved successfully to: {output_path}")
