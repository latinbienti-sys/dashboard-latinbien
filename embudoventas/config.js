/* Configuracion global del Embudo de Ventas (local).
   Edite estos valores o sobreescribalos por URL: index.html?corte=2026-10-05 */
var CONFIG = {
  /* Fecha corte maxima de los selectores "Desde"/"Hasta".
     'auto'             -> dia 03 del mes actual (limite por defecto).
     'YYYY-MM-DD'       -> fecha fija elegida por el usuario.
     Tambien por URL:   ?corte=YYYY-MM-DD                         */
  MAX_FECHA_CORTE: 'auto',

  /* Segundos entre recargas automaticas del cache_live.json (badge en vivo). */
  AUTO_REFRESH_SEG: 60,

  /* Meta diaria de gestiones para el semaforo de la tabla CREDIMOTOS. */
  META_LC_DIA: 5,

  /* Meta diaria total por ejecutivo para los semaforos.
     0 = automatico (suma de meta_diaria del embudo). */
  META_DIA_TOTAL: 0,

  /* Ejecutivos que NO se agregan automaticamente desde el sync en vivo
     (pools / bases de datos). Coincidencia por uid o por nombre exacto. */
  EXCLUIR_EJECUTIVOS: ['97', '130']
};
