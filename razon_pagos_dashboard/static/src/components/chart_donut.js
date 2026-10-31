/** @odoo-module **/

import { Component, onMounted, onPatched, onWillUnmount, useRef } from "@odoo/owl";
import { Chart } from "@web/core/chart/chart";

export function palette(n) {
    const base = [
        "#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed",
        "#0891b2", "#db2777", "#65a30d", "#ea580c", "#4f46e5",
        "#0d9488", "#be123c", "#a16207", "#15803d", "#9333ea",
    ];
    const out = [];
    for (let i = 0; i < Math.max(n, 1); i++) {
        out.push(base[i % base.length]);
    }
    return out;
}

function sliceLabelsPlugin() {
    return {
        id: "oRazonSliceLabels",
        afterDatasetsDraw(chart) {
            const meta = chart.getDatasetMeta(0);
            const data = chart.data.datasets[0].data;
            const total = data.reduce((acc, v) => acc + (Number(v) || 0), 0);
            if (!total || !meta.data.length) {
                return;
            }
            const ctx = chart.ctx;
            ctx.save();
            meta.data.forEach((arc, i) => {
                const pct = ((Number(data[i]) || 0) / total) * 100;
                if (pct < 4) {
                    return;
                }
                const radius = (arc.innerRadius + arc.outerRadius) / 2;
                const angle = (arc.startAngle + arc.endAngle) / 2;
                const x = arc.x + Math.cos(angle) * radius;
                const y = arc.y + Math.sin(angle) * radius;
                ctx.fillStyle = "#ffffff";
                ctx.font = "700 11px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(`${pct.toFixed(0)}%`, x, y);
            });
            ctx.restore();
        },
    };
}

export class DonutChart extends Component {
    static template = "razon_pagos_dashboard.DonutChart";
    static props = {
        rows: { type: Array, optional: true },
        totalLabel: { type: String, optional: true },
        totalCaption: { type: String, optional: true },
        onSliceClick: { type: Function, optional: true },
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        this._sig = null;
        onMounted(() => this.render());
        onPatched(() => this.render());
        onWillUnmount(() => this.destroy());
    }

    get rows() {
        return (this.props.rows || []).filter((r) => Number(r.value) > 0);
    }

    get signature() {
        const rows = this.rows;
        return `${rows.map((r) => `${r.key}:${r.label}:${Number(r.value) || 0}`).join("|")}::${this.props.totalLabel || ""}`;
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    render() {
        const el = this.canvasRef.el;
        if (!el) {
            return;
        }
        const sig = this.signature;
        if (this.chart && sig === this._sig) {
            return;
        }
        this._sig = sig;
        this.destroy();
        const rows = this.rows;
        const self = this;
        const centerPlugin = {
            id: "oRazonCenterText",
            afterDatasetsDraw(chart) {
                const meta = chart.getDatasetMeta(0);
                const area = chart.chartArea;
                if (!meta.data.length || !area) {
                    return;
                }
                const x = (area.left + area.right) / 2;
                const y = (area.top + area.bottom) / 2;
                const ctx = chart.ctx;
                ctx.save();
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#9ca3af";
                ctx.font = "600 11px sans-serif";
                ctx.fillText(self.props.totalCaption || "", x, y - 11);
                ctx.fillStyle = "#111827";
                ctx.font = "700 17px sans-serif";
                ctx.fillText(self.props.totalLabel || "", x, y + 9);
                ctx.restore();
            },
        };
        this.chart = new Chart(el.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: rows.map((r) => r.label),
                datasets: [
                    {
                        data: rows.map((r) => Number(r.value) || 0),
                        backgroundColor: palette(rows.length),
                        borderColor: "#ffffff",
                        borderWidth: 2,
                        hoverOffset: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "58%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 11, padding: 10, font: { size: 11 } },
                    },
                    tooltip: {
                        callbacks: {
                            label(item) {
                                const values = item.dataset.data;
                                const total = values.reduce((acc, v) => acc + (Number(v) || 0), 0);
                                const value = Number(item.raw) || 0;
                                const pct = total ? (value / total) * 100 : 0;
                                return ` ${item.label}: ${value.toFixed(2)} (${pct.toFixed(1)}%)`;
                            },
                        },
                    },
                },
                onClick(_evt, elements) {
                    if (elements.length && self.props.onSliceClick) {
                        self.props.onSliceClick(rows[elements[0].index]);
                    }
                },
            },
            plugins: [sliceLabelsPlugin(), centerPlugin],
        });
    }
}