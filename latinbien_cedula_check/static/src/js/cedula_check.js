(function () {
    'use strict';

    var TEXTS = {
        existe_con_linea: [
            '#e7f5e9', '#1b5e20',
            '¡Ya eres cliente con una línea de crédito activa! Un asesor te contactará para ayudarte.',
        ],
        existe_sin_linea: [
            '#e8f0fe', '#174ea6',
            'Ya te conocemos. Completa tu solicitud para continuar con tu evaluación.',
        ],
        no_existe: [
            '#f8f9fa', '#495057',
            'Continúa con tu solicitud para iniciar tu evaluación de crédito.',
        ],
    };

    function rpc(ident, num) {
        return fetch('/latinbien/cedula_check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0', method: 'call', id: Date.now(),
                params: { ident: ident, num: num },
            }),
        }).then(function (r) { return r.json(); }).then(function (j) {
            return (j && j.result) ? j.result.estado : 'error';
        }).catch(function () { return 'error'; });
    }

    function init() {
        var numEl = document.querySelector('[name="x_contenido_rif"]');
        if (!numEl) return;
        var form = numEl.closest('form');
        var identEl = form ? form.querySelector('[name="x_indentificador_rif"]') : null;
        var numWrap = numEl.closest('.s_website_form_field') || numEl;
        var fields = form ? [].slice.call(form.querySelectorAll('.s_website_form_field')) : [];

        var banner = document.createElement('div');
        banner.style.display = 'none';
        banner.style.padding = '14px 16px';
        banner.style.borderRadius = '10px';
        banner.style.margin = '0 0 16px';
        banner.style.fontWeight = '600';
        banner.style.lineHeight = '1.4';
        numWrap.parentNode.insertBefore(banner, numWrap);

        var link = document.createElement('a');
        link.href = '#';
        link.textContent = 'Mostrar formulario';
        link.style.marginLeft = '6px';
        link.style.textDecoration = 'underline';

        function setFieldsVisible(visible) {
            fields.forEach(function (f) {
                if (f === numWrap) return;
                f.style.display = visible ? '' : 'none';
            });
        }

        function show(estado) {
            if (estado === 'rate_limited' || estado === 'error') { banner.style.display = 'none'; setFieldsVisible(true); return; }
            var t = TEXTS[estado];
            if (!t) return;
            banner.style.display = 'block';
            banner.style.background = t[0];
            banner.style.color = t[1];
            banner.textContent = t[2];
            if (estado === 'existe_con_linea') {
                setFieldsVisible(false);
                banner.appendChild(link);
            } else {
                setFieldsVisible(true);
            }
        }

        link.addEventListener('click', function (e) {
            e.preventDefault();
            setFieldsVisible(true);
            banner.style.display = 'none';
        });

        var timer = null;
        function run() {
            var num = (numEl.value || '').replace(/\D/g, '');
            if (num.length < 6) { banner.style.display = 'none'; setFieldsVisible(true); return; }
            var ident = (identEl && identEl.value) ? identEl.value : 'V';
            rpc(ident, num).then(show);
        }
        function schedule() { clearTimeout(timer); timer = setTimeout(run, 600); }

        numEl.addEventListener('blur', schedule);
        numEl.addEventListener('change', schedule);
        if (identEl) identEl.addEventListener('change', schedule);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
