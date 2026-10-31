# -*- coding: utf-8 -*-
import logging

from odoo import _, api, models

_logger = logging.getLogger(__name__)

DEFAULT_MODELS = ["account.payment", "account.move.line", "account.move"]
DEFAULT_REASON_FIELDS = ["x_razonpagos"]
DEFAULT_MEASURE_FIELDS = ["amount", "amount_total", "debit", "debit_balance", "balance"]
DEFAULT_DATE_FIELDS = ["payment_date", "date", "invoice_date"]
DEFAULT_STATE_FIELDS = ["state", "parent_state", "payment_state"]
DEFAULT_PAYMENT_TYPE_FIELDS = ["payment_type"]
DOC_FIELDS = ["name", "ref", "move_id"]


class RazonPagosDashboard(models.AbstractModel):
    _name = "razon.pagos.dashboard"
    _description = "Analisis de pagos y egresos por Razon de pago"

    @api.model
    def _param(self, key, default=""):
        return self.env["ir.config_parameter"].sudo().get_param(key, default) or default

    @api.model
    def _csv(self, key, fallback):
        raw = self._param(key)
        items = [x.strip() for x in raw.split(",") if x.strip()]
        return items or list(fallback)

    @api.model
    def _pick(self, model_name, configured, candidates):
        fget = self.env[model_name].fields_get()
        if configured and configured in fget:
            return configured
        for cand in candidates:
            if cand in fget:
                return cand
        return False

    @api.model
    def _resolve(self):
        for model_name in self._csv("razon_pagos_dashboard.models", DEFAULT_MODELS):
            if model_name not in self.env:
                continue
            fget = self.env[model_name].fields_get()
            for fname in self._csv("razon_pagos_dashboard.reason_fields", DEFAULT_REASON_FIELDS):
                if fname in fget:
                    return {
                        "model": model_name,
                        "reason_field": fname,
                        "meta": fget[fname],
                        "measure": self._pick(
                            model_name,
                            self._param("razon_pagos_dashboard.measure"),
                            DEFAULT_MEASURE_FIELDS,
                        ),
                        "date_field": self._pick(
                            model_name,
                            self._param("razon_pagos_dashboard.date_field"),
                            DEFAULT_DATE_FIELDS,
                        ),
                        "state_field": self._pick(
                            model_name,
                            self._param("razon_pagos_dashboard.state_field"),
                            DEFAULT_STATE_FIELDS,
                        ),
                        "payment_type_field": self._pick(
                            model_name,
                            self._param("razon_pagos_dashboard.payment_type_field"),
                            DEFAULT_PAYMENT_TYPE_FIELDS,
                        ),
                    }
        return {}

    @api.model
    def _selection_map(self, cfg, fieldname):
        fld = self.env[cfg["model"]]._fields.get(fieldname)
        if fld is None:
            return {}
        items = None
        try:
            items = fld._description_selection(self.env)
        except Exception:
            items = getattr(fld, "selection", None)
            if isinstance(items, str):
                try:
                    items = getattr(self.env[cfg["model"]], items)()
                except Exception:
                    items = []
        out = {}
        for item in items or []:
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                out[item[0]] = item[1]
            else:
                out[item] = str(item)
        return out

    @api.model
    def _labels(self, cfg, groupby, keys):
        keys = [k for k in keys if k not in (False, None)]
        if not keys:
            return {}
        fget = self.env[cfg["model"]].fields_get([groupby])
        fmeta = fget.get(groupby) or {}
        if fmeta.get("type") == "selection":
            sel = self._selection_map(cfg, groupby)
            return {k: sel.get(k, str(k)) for k in keys}
        if fmeta.get("type") == "many2one":
            comodel = self.env[fmeta.get("relation")].sudo()
            try:
                recs = comodel.browse([int(k) for k in keys])
                return {r.id: r.display_name for r in recs}
            except Exception:
                _logger.warning("No se pudieron resolver etiquetas de %s", groupby)
                return {}
        return {k: str(k) for k in keys}

    @api.model
    def _date_bounds(self, cfg):
        df = cfg.get("date_field")
        if not df:
            return "", ""
        Model = self.env[cfg["model"]]
        try:
            recs = Model.search([], order=df, limit=1)
            lo = str(recs[0][df]) if recs and recs[0][df] else ""
            recs = Model.search([], order="%s desc" % df, limit=1)
            hi = str(recs[0][df]) if recs and recs[0][df] else ""
            return lo, hi
        except Exception:
            return "", ""

    @api.model
    def _currency_info(self, cfg):
        currency = self.env.company.currency_id
        measure = cfg.get("measure")
        fld = self.env[cfg["model"]]._fields.get(measure) if measure else None
        cf = getattr(fld, "currency_field", None) if fld else None
        if cf:
            try:
                rec = self.env[cfg["model"]].search([], limit=1)
                if rec and rec[cf]:
                    currency = rec[cf]
            except Exception:
                pass
        return {
            "id": currency.id,
            "name": currency.name or "",
            "symbol": currency.symbol or currency.name or "$",
            "position": currency.position or "after",
            "decimal_separator": currency.decimal_separator or ".",
            "thousands_sep": currency.thousands_sep or ",",
            "currency_unit_label": currency.currency_unit_label or "",
        }

    @api.model
    def _categories(self, cfg):
        fmeta = cfg["meta"]
        if fmeta.get("type") == "selection":
            return [{"key": k, "label": v} for k, v in self._selection_map(cfg, cfg["reason_field"]).items()]
        if fmeta.get("type") == "many2one":
            comodel = self.env[fmeta.get("relation")].sudo()
            try:
                recs = comodel.search([], order="display_name", limit=500)
            except Exception:
                recs = comodel.browse([])
            return [{"key": r.id, "label": r.display_name} for r in recs]
        return []

    @api.model
    def _levels(self, cfg):
        fget = self.env[cfg["model"]].fields_get()
        levels = []
        if "partner_id" in fget:
            levels.append({"field": "partner_id", "label": _("Proveedor / Beneficiario")})
        for cand in DOC_FIELDS:
            if cand in fget:
                levels.append({"field": cand, "label": _("Documento")})
                break
        return levels

    @api.model
    def get_config(self):
        cfg = self._resolve()
        if not cfg:
            return {
                "ok": False,
                "message": _(
                    "No se encontró el campo de Razón de pagos en ningún modelo. "
                    "Revisa la configuración del tablero."
                ),
                "models_tried": self._csv("razon_pagos_dashboard.models", DEFAULT_MODELS),
                "fields_tried": self._csv("razon_pagos_dashboard.reason_fields", DEFAULT_REASON_FIELDS),
            }
        Model = self.env[cfg["model"]]
        fget = Model.fields_get()
        measure = cfg.get("measure")
        date_field = cfg.get("date_field")
        state_field = cfg.get("state_field")
        ptype_field = cfg.get("payment_type_field")
        lo, hi = self._date_bounds(cfg)
        return {
            "ok": True,
            "model": cfg["model"],
            "model_label": Model._description,
            "reason_field": cfg["reason_field"],
            "reason_label": cfg["meta"].get("string") or cfg["reason_field"],
            "reason_type": cfg["meta"].get("type"),
            "measure": measure,
            "measure_label": (fget.get(measure) or {}).get("string") or measure,
            "date_field": date_field,
            "date_label": (fget.get(date_field) or {}).get("string") or date_field,
            "state_field": state_field,
            "state_values": [
                {"key": k, "label": v}
                for k, v in self._selection_map(cfg, state_field).items()
            ] if state_field else [],
            "payment_type_field": ptype_field,
            "payment_type_values": [
                {"key": k, "label": v}
                for k, v in self._selection_map(cfg, ptype_field).items()
            ] if ptype_field else [],
            "categories": self._categories(cfg),
            "levels": self._levels(cfg),
            "date_min": lo,
            "date_max": hi,
            "currency": self._currency_info(cfg),
        }

    @api.model
    def build_domain(self, cfg, payload):
        payload = payload or {}
        domain = []
        state_field = cfg.get("state_field")
        states = payload.get("states") or ["posted"]
        if state_field and states and "all" not in states:
            domain += [(state_field, "in", states)]
        ptype_field = cfg.get("payment_type_field")
        ptype = payload.get("payment_type")
        if ptype_field and ptype and ptype != "all":
            domain += [(ptype_field, "=", ptype)]
        date_field = cfg.get("date_field")
        if date_field and payload.get("date_from"):
            domain += [(date_field, ">=", payload["date_from"])]
        if date_field and payload.get("date_to"):
            domain += [(date_field, "<=", payload["date_to"])]
        reasons = payload.get("reasons") or []
        if cfg.get("reason_field") and reasons:
            domain += [(cfg["reason_field"], "in", reasons)]
        extra = payload.get("extra_domain") or []
        domain += list(extra)
        return domain

    @api.model
    def get_summary(self, cfg, domain):
        Model = self.env[cfg["model"]]
        measure = cfg["measure"]
        total = 0.0
        count = 0
        try:
            agg = Model.read_group(domain, [measure], [])
            if agg:
                total = agg[0].get(measure) or 0.0
            count = Model.search_count(domain)
        except Exception as exc:
            _logger.warning("get_summary fallo: %s", exc)
        return {
            "total": total,
            "count": count,
            "avg": (total / count) if count else 0.0,
        }

    @api.model
    def get_breakdown(self, cfg, groupby, domain, limit=0, offset=0, order=""):
        Model = self.env[cfg["model"]]
        measure = cfg["measure"]
        try:
            groups = Model.read_group(
                domain,
                [measure],
                [groupby],
                offset=offset,
                limit=limit,
                orderby=order or False,
                lazy=False,
            )
        except Exception as exc:
            _logger.warning("get_breakdown fallo en %s: %s", groupby, exc)
            return {"rows": []}
        labels = self._labels(cfg, groupby, [g.get(groupby) for g in groups])
        rows = []
        for g in groups:
            key = g.get(groupby)
            rows.append({
                "key": key if key not in (False, None) else False,
                "label": labels.get(key) or _("(Sin clasificar)"),
                "value": g.get(measure) or 0.0,
                "count": g.get("__count") or 0,
                "domain": g.get("__domain") or [],
            })
        return {"rows": rows}