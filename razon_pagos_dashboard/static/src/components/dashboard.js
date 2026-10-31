/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formatMonetary } from "@web/core/l10n/currency";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props/standard_widget_props";
import { DonutChart } from "./chart_donut";

export class RazonPagosDashboard extends Component {
    static template = "razon_pagos_dashboard.Dashboard";
    static components = { DonutChart };
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            loading: true,
            error: null,
            config: null,
            filter: {
                date_from: "",
                date_to: "",
                states: ["posted"],
                reasons: [],
                payment_type: "outbound",
            },
            total: 0,
            count: 0,
            avg: 0,
            donut: [],
            rows: [],
            expanded: {},
            activeReason: null,
        });
        onWillStart(async () => {
            await this.load();
        });
    }

    get currency() {
        return (this.state.config && this.state.config.currency) || {};
    }

    money(value) {
        return formatMonetary(Number(value) || 0, this.currency);
    }

    pct(value) {
        return `${(Number(value) || 0).toFixed(1)}%`;
    }

    async load() {
        this.state.loading = true;
        this.state.error = null;
        try {
            const cfg = await this.orm.call("razon.pagos.dashboard", "get_config", []);
            if (!cfg.ok) {
                this.state.error = cfg;
                this.state.loading = false;
                return;
            }
            this.state.config = cfg;
            this.state.filter.date_from = cfg.date_min || "";
            this.state.filter.date_to = cfg.date_max || "";
            this.state.filter.payment_type = cfg.payment_type_field ? "outbound" : "all";
            await this.refresh();
        } catch (err) {
            this.state.error = { message: (err && err.data && err.data.message) || String(err) };
        }
        this.state.loading = false;
    }

    decorate(rows, level, parentPath, parentValue, grandTotal) {
        return (rows || []).map((row) => ({
            ...row,
            path: `${parentPath}|L${level}:${row.key}`,
            level,
            parentValue,
            pct: grandTotal ? ((Number(row.value) || 0) / grandTotal) * 100 : 0,
            children: null,
        }));
    }

    async refresh() {
        const cfg = this.state.config;
        if (!cfg) {
            return;
        }
        const domain = await this.orm.call("razon.pagos.dashboard", "build_domain", [cfg, this.state.filter]);
        const [summary, breakdown] = await Promise.all([
            this.orm.call("razon.pagos.dashboard", "get_summary", [cfg, domain]),
            this.orm.call("razon.pagos.dashboard", "get_breakdown", [cfg, cfg.reason_field, domain, 0, 0, ""]),
        ]);
        this.state.total = summary.total;
        this.state.count = summary.count;
        this.state.avg = summary.avg;
        this.state.donut = (breakdown.rows || [])
            .slice()
            .sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0));
        this.state.rows = this.decorate(breakdown.rows, 0, "", 0, summary.total);
        this.state.expanded = {};
        this.state.activeReason = null;
    }

    async onFilterChange() {
        this.state.loading = true;
        await this.refresh();
        this.state.loading = false;
    }

    onStateChange(ev) {
        const value = ev.target.value;
        this.state.filter.states = value === "all" ? [] : [value];
        this.onFilterChange();
    }

    onPaymentTypeChange(ev) {
        this.state.filter.payment_type = ev.target.value;
        this.onFilterChange();
    }

    async toggleReason(key) {
        const list = this.state.filter.reasons;
        const idx = list.indexOf(key);
        if (idx === -1) {
            list.push(key);
        } else {
            list.splice(idx, 1);
        }
        await this.onFilterChange();
    }

    clearReasons() {
        this.state.filter.reasons = [];
        this.onFilterChange();
    }

    setDefaults() {
        const cfg = this.state.config;
        this.state.filter.date_from = cfg.date_min || "";
        this.state.filter.date_to = cfg.date_max || "";
        this.onFilterChange();
    }

    setThisMonth() {
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, "0");
        this.state.filter.date_from = `${y}-${m}-01`;
        this.state.filter.date_to = `${y}-${m}-31`;
        this.onFilterChange();
    }

    setThisYear() {
        const y = new Date().getFullYear();
        this.state.filter.date_from = `${y}-01-01`;
        this.state.filter.date_to = `${y}-12-31`;
        this.onFilterChange();
    }

    async toggleNode(node) {
        const path = node.path;
        if (this.state.expanded[path]) {
            delete this.state.expanded[path];
            return;
        }
        this.state.expanded[path] = true;
        if (node.children !== null) {
            return;
        }
        const cfg = this.state.config;
        const nextLevel = (cfg.levels || [])[node.level + 1];
        if (!nextLevel) {
            return;
        }
        node.children = [];
        const domain = await this.orm.call("razon.pagos.dashboard", "build_domain", [
            cfg,
            Object.assign({}, this.state.filter, { extra_domain: node.domain }),
        ]);
        const res = await this.orm.call("razon.pagos.dashboard", "get_breakdown", [
            cfg,
            nextLevel.field,
            domain,
            0,
            0,
            "",
        ]);
        node.children = this.decorate(res.rows, node.level + 1, path, node.value, this.state.total);
    }

    get flatRows() {
        const out = [];
        const walk = (nodes, depth) => {
            for (const node of nodes) {
                out.push(Object.assign({}, node, { depth }));
                if (this.state.expanded[node.path] && node.children && node.children.length) {
                    walk(node.children, depth + 1);
                }
            }
        };
        walk(this.state.rows, 0);
        return out;
    }

    levelLabel(level) {
        const levels = (this.state.config && this.state.config.levels) || [];
        if (level === 0) {
            return (this.state.config && this.state.config.reason_label) || "Concepto";
        }
        const def = levels[level - 1];
        return def ? def.label : "";
    }

    hasChildren(node) {
        const levels = (this.state.config && this.state.config.levels) || [];
        return node.level < levels.length;
    }

    async filterByReason(row) {
        this.state.filter.reasons = [row.key];
        await this.onFilterChange();
        this.state.activeReason = row.label;
    }

    openList(domain, title) {
        const cfg = this.state.config;
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: title || cfg.model_label,
            res_model: cfg.model,
            views: [
                [false, "tree"],
                [false, "form"],
            ],
            domain: domain,
            context: { create: false, edit: false, delete: false },
            target: "current",
        });
    }

    openAll() {
        const cfg = this.state.config;
        return this.orm
            .call("razon.pagos.dashboard", "build_domain", [cfg, this.state.filter])
            .then((domain) => this.openList(domain, "Detalle de pagos y egresos"));
    }

    exportCsv() {
        const cfg = this.state.config;
        const rows = this.flatRows;
        const header = [
            "Nivel",
            cfg.reason_label || "Concepto",
            "Detalle",
            "Monto",
            "% Total",
            "Cantidad",
        ];
        const lines = [header.join(";")];
        for (const row of rows) {
            const detail = row.level === 0 ? "" : this.levelLabel(row.level);
            const indent = row.depth > 0 ? "  ".repeat(row.depth) : "";
            lines.push(
                [
                    row.level + 1,
                    `"${indent}${String(row.label).replace(/"/g, "'")}"`,
                    `"${detail}"`,
                    Number(row.value || 0).toFixed(2),
                    Number(row.pct || 0).toFixed(2),
                    row.count || 0,
                ].join(";")
            );
        }
        lines.push(["", `"TOTAL"`, "", Number(this.state.total || 0).toFixed(2), "100.00", this.state.count || 0].join(";"));
        const blob = new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `analisis_razon_pagos_${cfg.reason_field}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

registry.category("actions").add("razon_pagos.dashboard", RazonPagosDashboard);