--
-- PostgreSQL database dump
--

-- Dumped from database version 17.0
-- Dumped by pg_dump version 17.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: auditorias_calidad; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auditorias_calidad (
    id integer NOT NULL,
    reclamo_id integer NOT NULL,
    auditor_id integer,
    resultado character varying(30),
    tiempo_atencion_min integer,
    dentro_sla boolean,
    observaciones text,
    tecnico_nombre character varying(200),
    operador_nombre character varying(200),
    codigo_falla character varying(10),
    fecha_creacion_reclamo timestamp without time zone,
    fecha_cierre_reclamo timestamp without time zone,
    fecha_auditoria timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.auditorias_calidad OWNER TO postgres;

--
-- Name: auditorias_calidad_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auditorias_calidad_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auditorias_calidad_id_seq OWNER TO postgres;

--
-- Name: auditorias_calidad_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auditorias_calidad_id_seq OWNED BY public.auditorias_calidad.id;


--
-- Name: codigos_falla; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.codigos_falla (
    id integer NOT NULL,
    codigo character varying(10) NOT NULL,
    nombre character varying(150) NOT NULL,
    descripcion text,
    categoria character varying(80),
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.codigos_falla OWNER TO postgres;

--
-- Name: codigos_falla_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.codigos_falla_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.codigos_falla_id_seq OWNER TO postgres;

--
-- Name: codigos_falla_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.codigos_falla_id_seq OWNED BY public.codigos_falla.id;


--
-- Name: codigos_ivr_liberacion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.codigos_ivr_liberacion (
    id integer NOT NULL,
    servicio character varying(20) NOT NULL,
    medio character varying(20) NOT NULL,
    codigo_ivr character varying(10) NOT NULL,
    descripcion character varying(150),
    activo boolean DEFAULT true
);


ALTER TABLE public.codigos_ivr_liberacion OWNER TO postgres;

--
-- Name: codigos_ivr_liberacion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.codigos_ivr_liberacion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.codigos_ivr_liberacion_id_seq OWNER TO postgres;

--
-- Name: codigos_ivr_liberacion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.codigos_ivr_liberacion_id_seq OWNED BY public.codigos_ivr_liberacion.id;


--
-- Name: codigos_registro_cliente; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.codigos_registro_cliente (
    id integer NOT NULL,
    codigo character varying(5) NOT NULL,
    activo boolean DEFAULT true,
    usado boolean DEFAULT false,
    usuario_id integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_uso timestamp without time zone
);


ALTER TABLE public.codigos_registro_cliente OWNER TO postgres;

--
-- Name: codigos_registro_cliente_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.codigos_registro_cliente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.codigos_registro_cliente_id_seq OWNER TO postgres;

--
-- Name: codigos_registro_cliente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.codigos_registro_cliente_id_seq OWNED BY public.codigos_registro_cliente.id;


--
-- Name: codigos_registro_empleado; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.codigos_registro_empleado (
    id integer NOT NULL,
    codigo character varying(4) NOT NULL,
    rol character varying(30) NOT NULL,
    activo boolean DEFAULT true,
    usado boolean DEFAULT false,
    usuario_id integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_uso timestamp without time zone,
    id_rol integer
);


ALTER TABLE public.codigos_registro_empleado OWNER TO postgres;

--
-- Name: codigos_registro_empleado_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.codigos_registro_empleado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.codigos_registro_empleado_id_seq OWNER TO postgres;

--
-- Name: codigos_registro_empleado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.codigos_registro_empleado_id_seq OWNED BY public.codigos_registro_empleado.id;


--
-- Name: codigos_solucion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.codigos_solucion (
    id integer NOT NULL,
    codigo character varying(5) NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.codigos_solucion OWNER TO postgres;

--
-- Name: codigos_solucion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.codigos_solucion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.codigos_solucion_id_seq OWNER TO postgres;

--
-- Name: codigos_solucion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.codigos_solucion_id_seq OWNED BY public.codigos_solucion.id;


--
-- Name: contratos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contratos (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    numero_contrato character(8) NOT NULL,
    tipo_servicio character varying(100),
    direccion character varying(300),
    telefono_referencia character varying(20),
    telefono_factura character varying(20),
    zona_id integer,
    servicio_origen_id integer,
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT now(),
    CONSTRAINT contratos_numero_contrato_check CHECK ((numero_contrato ~ '^[0-9]{8}$'::text))
);


ALTER TABLE public.contratos OWNER TO postgres;

--
-- Name: contratos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contratos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contratos_id_seq OWNER TO postgres;

--
-- Name: contratos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contratos_id_seq OWNED BY public.contratos.id;


--
-- Name: cuentas_pago_tramites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cuentas_pago_tramites (
    id integer NOT NULL,
    tramite_id integer,
    codigo_cuenta character varying(50) NOT NULL,
    monto numeric(10,2) DEFAULT 0,
    estado character varying(20) DEFAULT 'activa'::character varying,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_pago timestamp without time zone
);


ALTER TABLE public.cuentas_pago_tramites OWNER TO postgres;

--
-- Name: cuentas_pago_tramites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cuentas_pago_tramites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cuentas_pago_tramites_id_seq OWNER TO postgres;

--
-- Name: cuentas_pago_tramites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cuentas_pago_tramites_id_seq OWNED BY public.cuentas_pago_tramites.id;


--
-- Name: diagnosticos_remotos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.diagnosticos_remotos (
    id integer NOT NULL,
    reclamo_id integer NOT NULL,
    operador_id integer,
    fecha_inicio timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_fin timestamp without time zone,
    reinicio_onu boolean DEFAULT false,
    validacion_potencia boolean DEFAULT false,
    reconfiguracion boolean DEFAULT false,
    reinicio_puerto boolean DEFAULT false,
    sincronizacion boolean DEFAULT false,
    cambio_perfil boolean DEFAULT false,
    otros boolean DEFAULT false,
    descripcion_otros text,
    observaciones text,
    solucionado boolean,
    codigo_falla_id integer,
    duracion_minutos integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    elemento_afectado_id integer
);


ALTER TABLE public.diagnosticos_remotos OWNER TO postgres;

--
-- Name: diagnosticos_remotos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.diagnosticos_remotos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.diagnosticos_remotos_id_seq OWNER TO postgres;

--
-- Name: diagnosticos_remotos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.diagnosticos_remotos_id_seq OWNED BY public.diagnosticos_remotos.id;


--
-- Name: elementos_red; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.elementos_red (
    id integer NOT NULL,
    codigo character varying(5) NOT NULL,
    nombre character varying(100) NOT NULL,
    activo boolean DEFAULT true
);


ALTER TABLE public.elementos_red OWNER TO postgres;

--
-- Name: elementos_red_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.elementos_red_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.elementos_red_id_seq OWNER TO postgres;

--
-- Name: elementos_red_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.elementos_red_id_seq OWNED BY public.elementos_red.id;


--
-- Name: empleados_soporte; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.empleados_soporte (
    id integer NOT NULL,
    usuario_id integer,
    nombre_completo character varying(200) NOT NULL,
    especialidad character varying(50) DEFAULT 'general'::character varying,
    carga_trabajo integer DEFAULT 0,
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.empleados_soporte OWNER TO postgres;

--
-- Name: empleados_soporte_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.empleados_soporte_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.empleados_soporte_id_seq OWNER TO postgres;

--
-- Name: empleados_soporte_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.empleados_soporte_id_seq OWNED BY public.empleados_soporte.id;


--
-- Name: facturas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.facturas (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    numero_factura character varying(50) NOT NULL,
    fecha_emision date NOT NULL,
    fecha_vencimiento date NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    impuestos numeric(10,2) DEFAULT 0,
    descuentos numeric(10,2) DEFAULT 0,
    total numeric(10,2) NOT NULL,
    estado character varying(20) DEFAULT 'pendiente'::character varying,
    fecha_pago timestamp without time zone,
    metodo_pago character varying(50),
    archivo_url character varying(255)
);


ALTER TABLE public.facturas OWNER TO postgres;

--
-- Name: facturas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.facturas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.facturas_id_seq OWNER TO postgres;

--
-- Name: facturas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.facturas_id_seq OWNED BY public.facturas.id;


--
-- Name: fallas_masivas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fallas_masivas (
    id integer NOT NULL,
    codigo character varying(30) NOT NULL,
    nombre character varying(200) NOT NULL,
    nodo character varying(150),
    sector character varying(150),
    descripcion text,
    codigo_falla_id integer,
    estado character varying(30) DEFAULT 'activa'::character varying,
    responsable_id integer,
    cuadrilla character varying(200),
    fecha_inicio timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_estimada timestamp without time zone,
    fecha_resolucion timestamp without time zone,
    ivr_notificado boolean DEFAULT false,
    fecha_ivr timestamp without time zone,
    clientes_afectados integer DEFAULT 0,
    observaciones text,
    creado_por integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.fallas_masivas OWNER TO postgres;

--
-- Name: fallas_masivas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fallas_masivas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fallas_masivas_id_seq OWNER TO postgres;

--
-- Name: fallas_masivas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fallas_masivas_id_seq OWNED BY public.fallas_masivas.id;


--
-- Name: feriados; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.feriados (
    id integer NOT NULL,
    fecha date NOT NULL,
    nombre character varying(150) NOT NULL
);


ALTER TABLE public.feriados OWNER TO postgres;

--
-- Name: feriados_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.feriados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.feriados_id_seq OWNER TO postgres;

--
-- Name: feriados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.feriados_id_seq OWNED BY public.feriados.id;


--
-- Name: historial_zona; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.historial_zona (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    zona_anterior_id integer,
    zona_nueva_id integer,
    modificado_por integer,
    tipo_accion character varying(30) NOT NULL,
    fecha timestamp without time zone DEFAULT now()
);


ALTER TABLE public.historial_zona OWNER TO postgres;

--
-- Name: historial_zona_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.historial_zona_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.historial_zona_id_seq OWNER TO postgres;

--
-- Name: historial_zona_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.historial_zona_id_seq OWNED BY public.historial_zona.id;


--
-- Name: notificaciones_enviadas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notificaciones_enviadas (
    id integer NOT NULL,
    usuario_id integer,
    tramite_id integer,
    tipo_notificacion character varying(100),
    metodo character varying(20),
    mensaje text,
    estado character varying(20) DEFAULT 'enviado'::character varying,
    fecha_envio timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.notificaciones_enviadas OWNER TO postgres;

--
-- Name: notificaciones_enviadas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notificaciones_enviadas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notificaciones_enviadas_id_seq OWNER TO postgres;

--
-- Name: notificaciones_enviadas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notificaciones_enviadas_id_seq OWNED BY public.notificaciones_enviadas.id;


--
-- Name: notificaciones_jefe; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notificaciones_jefe (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    reclamo_id integer,
    tipo character varying(50) DEFAULT 'nuevo_reclamo'::character varying,
    mensaje text NOT NULL,
    leida boolean DEFAULT false,
    fecha_creacion timestamp without time zone DEFAULT now()
);


ALTER TABLE public.notificaciones_jefe OWNER TO postgres;

--
-- Name: notificaciones_jefe_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notificaciones_jefe_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notificaciones_jefe_id_seq OWNER TO postgres;

--
-- Name: notificaciones_jefe_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notificaciones_jefe_id_seq OWNED BY public.notificaciones_jefe.id;


--
-- Name: notificaciones_soporte; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notificaciones_soporte (
    id integer NOT NULL,
    empleado_id integer,
    reclamo_id integer,
    tramite_id integer,
    tipo_notificacion character varying(100),
    mensaje text,
    leida boolean DEFAULT false,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.notificaciones_soporte OWNER TO postgres;

--
-- Name: notificaciones_soporte_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notificaciones_soporte_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notificaciones_soporte_id_seq OWNER TO postgres;

--
-- Name: notificaciones_soporte_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notificaciones_soporte_id_seq OWNED BY public.notificaciones_soporte.id;


--
-- Name: ordenes_trabajo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ordenes_trabajo (
    id integer NOT NULL,
    numero_ot character varying(20) NOT NULL,
    titulo character varying(200) NOT NULL,
    descripcion text,
    tipo_trabajo character varying(100),
    prioridad character varying(20) DEFAULT 'media'::character varying,
    estado character varying(30) DEFAULT 'pendiente'::character varying,
    tecnico_id integer,
    usuario_cliente_id integer,
    direccion character varying(300),
    coordenadas character varying(100),
    fecha_programada timestamp without time zone,
    fecha_inicio timestamp without time zone,
    fecha_fin timestamp without time zone,
    observaciones text,
    creado_por integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    reclamo_id integer,
    codigo_solucion_id integer,
    area_dato_tecnico character varying(100),
    fecha_1er_informe timestamp without time zone,
    fecha_2do_informe timestamp without time zone,
    informe_1_detalle text,
    informe_2_detalle text
);


ALTER TABLE public.ordenes_trabajo OWNER TO postgres;

--
-- Name: ordenes_trabajo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ordenes_trabajo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ordenes_trabajo_id_seq OWNER TO postgres;

--
-- Name: ordenes_trabajo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ordenes_trabajo_id_seq OWNED BY public.ordenes_trabajo.id;


--
-- Name: ot_actividades; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ot_actividades (
    id integer NOT NULL,
    ot_id integer,
    tecnico_id integer,
    descripcion text NOT NULL,
    tipo character varying(50) DEFAULT 'nota'::character varying,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.ot_actividades OWNER TO postgres;

--
-- Name: ot_actividades_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ot_actividades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ot_actividades_id_seq OWNER TO postgres;

--
-- Name: ot_actividades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ot_actividades_id_seq OWNED BY public.ot_actividades.id;


--
-- Name: pagos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pagos (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    factura_id integer,
    monto numeric(10,2) NOT NULL,
    fecha_pago timestamp without time zone DEFAULT now(),
    metodo_pago character varying(50),
    estado character varying(20) DEFAULT 'completado'::character varying,
    referencia character varying(100)
);


ALTER TABLE public.pagos OWNER TO postgres;

--
-- Name: pagos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pagos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pagos_id_seq OWNER TO postgres;

--
-- Name: pagos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pagos_id_seq OWNED BY public.pagos.id;


--
-- Name: reclamos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reclamos (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo_reclamo character varying(100) NOT NULL,
    titulo character varying(200) NOT NULL,
    descripcion text NOT NULL,
    estado character varying(40) DEFAULT 'abierto'::character varying,
    prioridad character varying(20) DEFAULT 'media'::character varying,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_asignacion timestamp without time zone,
    fecha_resolucion timestamp without time zone,
    asignado_a integer,
    solucion text,
    satisfaccion integer,
    comentarios_cliente text,
    servicio_afectado character varying(100),
    problema_especifico character varying(200),
    ubicacion_cliente character varying(300),
    numero_cliente character varying(50),
    estado_cuenta character varying(50) DEFAULT 'al_dia'::character varying,
    monto_adeudado numeric(10,2) DEFAULT 0.00,
    nota_tecnico text,
    codigo_falla_id integer,
    zona_nodo character varying(100),
    zona_olt character varying(100),
    zona_puerto character varying(50),
    zona_caja character varying(100),
    zona_distrito character varying(100),
    codigo_abonado character varying(100),
    resuelto_remotamente boolean DEFAULT false,
    falla_masiva_id integer,
    liberado_ivr boolean DEFAULT false,
    fecha_liberacion_ivr timestamp without time zone,
    tiempo_diagnostico_min integer,
    tiempo_resolucion_min integer,
    fecha_diagnostico_inicio timestamp without time zone,
    fecha_diagnostico_fin timestamp without time zone,
    origen_reclamo character varying(20) DEFAULT 'web'::character varying,
    registrado_por integer,
    medio_fisico character varying(20),
    instancia integer DEFAULT 1,
    falla_energia_refrigeracion boolean DEFAULT false,
    codigo_ivr_usado character varying(10),
    escalado_a character varying(30),
    fecha_escalacion timestamp without time zone,
    veces_rechazado integer DEFAULT 0,
    motivo_rechazo text,
    elemento_afectado_id integer,
    telefono_referencia character varying(20),
    ubicacion_lat numeric(10,6),
    ubicacion_lng numeric(10,6),
    fuera_de_horario boolean DEFAULT false,
    es_turno_nocturno boolean DEFAULT false,
    CONSTRAINT reclamos_escalado_a_check CHECK (((escalado_a IS NULL) OR ((escalado_a)::text = ANY ((ARRAY['transmisiones'::character varying, 'telefonia'::character varying, 'tv_cable'::character varying, 'internet'::character varying, 'nodo_internet'::character varying])::text[])))),
    CONSTRAINT reclamos_instancia_check CHECK ((instancia = ANY (ARRAY[1, 2]))),
    CONSTRAINT reclamos_medio_fisico_check CHECK (((medio_fisico IS NULL) OR ((medio_fisico)::text = ANY ((ARRAY['fibra_optica'::character varying, 'coaxial'::character varying, 'cobre'::character varying])::text[])))),
    CONSTRAINT reclamos_satisfaccion_check CHECK (((satisfaccion >= 1) AND (satisfaccion <= 5)))
);


ALTER TABLE public.reclamos OWNER TO postgres;

--
-- Name: reclamos_fallas_masivas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reclamos_fallas_masivas (
    id integer NOT NULL,
    reclamo_id integer NOT NULL,
    falla_masiva_id integer NOT NULL,
    fecha_asociacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.reclamos_fallas_masivas OWNER TO postgres;

--
-- Name: reclamos_fallas_masivas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reclamos_fallas_masivas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reclamos_fallas_masivas_id_seq OWNER TO postgres;

--
-- Name: reclamos_fallas_masivas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reclamos_fallas_masivas_id_seq OWNED BY public.reclamos_fallas_masivas.id;


--
-- Name: reclamos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reclamos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reclamos_id_seq OWNER TO postgres;

--
-- Name: reclamos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reclamos_id_seq OWNED BY public.reclamos.id;


--
-- Name: reclamos_seguimiento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reclamos_seguimiento (
    id integer NOT NULL,
    reclamo_id integer,
    empleado_id integer,
    accion character varying(100),
    descripcion text,
    fecha_accion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.reclamos_seguimiento OWNER TO postgres;

--
-- Name: reclamos_seguimiento_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reclamos_seguimiento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reclamos_seguimiento_id_seq OWNER TO postgres;

--
-- Name: reclamos_seguimiento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reclamos_seguimiento_id_seq OWNED BY public.reclamos_seguimiento.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id_rol integer NOT NULL,
    rol character varying(50) NOT NULL,
    descripcion text,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    activo boolean DEFAULT true
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_id_rol_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_id_rol_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_rol_seq OWNER TO postgres;

--
-- Name: roles_id_rol_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_id_rol_seq OWNED BY public.roles.id_rol;


--
-- Name: seq_numero_fm; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.seq_numero_fm
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.seq_numero_fm OWNER TO postgres;

--
-- Name: seq_numero_ot; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.seq_numero_ot
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.seq_numero_ot OWNER TO postgres;

--
-- Name: servicios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.servicios (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo_servicio character varying(50) NOT NULL,
    numero_servicio character varying(50) NOT NULL,
    plan character varying(100),
    estado character varying(20) DEFAULT 'activo'::character varying,
    fecha_contratacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_activacion timestamp without time zone,
    fecha_suspension timestamp without time zone,
    monto_mensual numeric(10,2),
    descripcion text,
    direccion_instalacion character varying(300)
);


ALTER TABLE public.servicios OWNER TO postgres;

--
-- Name: COLUMN servicios.direccion_instalacion; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.servicios.direccion_instalacion IS 'Dirección física donde está instalado ESTE contrato/servicio.';


--
-- Name: servicios_disponibles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.servicios_disponibles (
    id integer NOT NULL,
    nombre_servicio character varying(100) NOT NULL,
    categoria character varying(50) NOT NULL,
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.servicios_disponibles OWNER TO postgres;

--
-- Name: servicios_disponibles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.servicios_disponibles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.servicios_disponibles_id_seq OWNER TO postgres;

--
-- Name: servicios_disponibles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.servicios_disponibles_id_seq OWNED BY public.servicios_disponibles.id;


--
-- Name: servicios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.servicios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.servicios_id_seq OWNER TO postgres;

--
-- Name: servicios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.servicios_id_seq OWNED BY public.servicios.id;


--
-- Name: tecnicos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tecnicos (
    id integer NOT NULL,
    usuario_id integer,
    especialidad character varying(100),
    zona_asignada character varying(100),
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tipo_tecnico character varying(2),
    servicio_tecnico character varying(20),
    medio_tecnico character varying(20),
    instancia_tecnico integer DEFAULT 1,
    zona_id integer,
    CONSTRAINT tecnicos_instancia_tecnico_check CHECK ((instancia_tecnico = ANY (ARRAY[1, 2]))),
    CONSTRAINT tecnicos_medio_tecnico_check CHECK (((medio_tecnico IS NULL) OR ((medio_tecnico)::text = ANY ((ARRAY['fibra_optica'::character varying, 'coaxial'::character varying, 'cobre'::character varying])::text[])))),
    CONSTRAINT tecnicos_servicio_tecnico_check CHECK (((servicio_tecnico IS NULL) OR ((servicio_tecnico)::text = ANY ((ARRAY['telefonia'::character varying, 'tv_cable'::character varying, 'internet'::character varying, 'transmisiones'::character varying])::text[])))),
    CONSTRAINT tecnicos_tipo_tecnico_check CHECK ((((tipo_tecnico)::text = ANY ((ARRAY['RA'::character varying, 'RC'::character varying])::text[])) OR (tipo_tecnico IS NULL)))
);


ALTER TABLE public.tecnicos OWNER TO postgres;

--
-- Name: tecnicos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tecnicos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tecnicos_id_seq OWNER TO postgres;

--
-- Name: tecnicos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tecnicos_id_seq OWNED BY public.tecnicos.id;


--
-- Name: tipos_problemas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tipos_problemas (
    id integer NOT NULL,
    servicio_id integer,
    nombre_problema character varying(200) NOT NULL,
    descripcion_problema text,
    categoria character varying(50),
    activo boolean DEFAULT true,
    solucion_sugerida text
);


ALTER TABLE public.tipos_problemas OWNER TO postgres;

--
-- Name: tipos_problemas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tipos_problemas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_problemas_id_seq OWNER TO postgres;

--
-- Name: tipos_problemas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tipos_problemas_id_seq OWNED BY public.tipos_problemas.id;


--
-- Name: trabajos_reparados; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.trabajos_reparados (
    id integer NOT NULL,
    ot_id integer,
    reclamo_id integer,
    tecnico_id integer,
    numero_ot character varying(20),
    servicio character varying(20),
    medio character varying(20),
    instancia integer,
    codigo_ivr character varying(10),
    fecha_inicio timestamp without time zone,
    fecha_fin timestamp without time zone DEFAULT now(),
    duracion_min integer,
    fecha_registro timestamp without time zone DEFAULT now()
);


ALTER TABLE public.trabajos_reparados OWNER TO postgres;

--
-- Name: TABLE trabajos_reparados; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.trabajos_reparados IS 'Bitácora de trabajos completados por técnicos. Se llena automáticamente al marcar una OT como completado.';


--
-- Name: trabajos_reparados_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.trabajos_reparados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.trabajos_reparados_id_seq OWNER TO postgres;

--
-- Name: trabajos_reparados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.trabajos_reparados_id_seq OWNED BY public.trabajos_reparados.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    usuario_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido character varying(100) NOT NULL,
    correo character varying(150) NOT NULL,
    "contraseña" character varying(255) NOT NULL,
    telefono character varying(20) NOT NULL,
    codigo_verificacion character varying(255),
    verificado boolean DEFAULT false,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    token_recuperacion character varying(255),
    ultimo_inicio_sesion timestamp without time zone,
    activo boolean DEFAULT true,
    id_rol integer NOT NULL,
    zona_id integer,
    foto_perfil character varying(255)
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Name: usuarios_usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_usuario_id_seq OWNER TO postgres;

--
-- Name: usuarios_usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_usuario_id_seq OWNED BY public.usuarios.usuario_id;


--
-- Name: zonas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.zonas (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    activo boolean DEFAULT true
);


ALTER TABLE public.zonas OWNER TO postgres;

--
-- Name: zonas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.zonas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.zonas_id_seq OWNER TO postgres;

--
-- Name: zonas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.zonas_id_seq OWNED BY public.zonas.id;


--
-- Name: auditorias_calidad id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditorias_calidad ALTER COLUMN id SET DEFAULT nextval('public.auditorias_calidad_id_seq'::regclass);


--
-- Name: codigos_falla id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_falla ALTER COLUMN id SET DEFAULT nextval('public.codigos_falla_id_seq'::regclass);


--
-- Name: codigos_ivr_liberacion id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_ivr_liberacion ALTER COLUMN id SET DEFAULT nextval('public.codigos_ivr_liberacion_id_seq'::regclass);


--
-- Name: codigos_registro_cliente id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_cliente ALTER COLUMN id SET DEFAULT nextval('public.codigos_registro_cliente_id_seq'::regclass);


--
-- Name: codigos_registro_empleado id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_empleado ALTER COLUMN id SET DEFAULT nextval('public.codigos_registro_empleado_id_seq'::regclass);


--
-- Name: codigos_solucion id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_solucion ALTER COLUMN id SET DEFAULT nextval('public.codigos_solucion_id_seq'::regclass);


--
-- Name: contratos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos ALTER COLUMN id SET DEFAULT nextval('public.contratos_id_seq'::regclass);


--
-- Name: cuentas_pago_tramites id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cuentas_pago_tramites ALTER COLUMN id SET DEFAULT nextval('public.cuentas_pago_tramites_id_seq'::regclass);


--
-- Name: diagnosticos_remotos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnosticos_remotos ALTER COLUMN id SET DEFAULT nextval('public.diagnosticos_remotos_id_seq'::regclass);


--
-- Name: elementos_red id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.elementos_red ALTER COLUMN id SET DEFAULT nextval('public.elementos_red_id_seq'::regclass);


--
-- Name: empleados_soporte id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.empleados_soporte ALTER COLUMN id SET DEFAULT nextval('public.empleados_soporte_id_seq'::regclass);


--
-- Name: facturas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas ALTER COLUMN id SET DEFAULT nextval('public.facturas_id_seq'::regclass);


--
-- Name: fallas_masivas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallas_masivas ALTER COLUMN id SET DEFAULT nextval('public.fallas_masivas_id_seq'::regclass);


--
-- Name: feriados id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feriados ALTER COLUMN id SET DEFAULT nextval('public.feriados_id_seq'::regclass);


--
-- Name: historial_zona id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_zona ALTER COLUMN id SET DEFAULT nextval('public.historial_zona_id_seq'::regclass);


--
-- Name: notificaciones_enviadas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_enviadas ALTER COLUMN id SET DEFAULT nextval('public.notificaciones_enviadas_id_seq'::regclass);


--
-- Name: notificaciones_jefe id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_jefe ALTER COLUMN id SET DEFAULT nextval('public.notificaciones_jefe_id_seq'::regclass);


--
-- Name: notificaciones_soporte id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_soporte ALTER COLUMN id SET DEFAULT nextval('public.notificaciones_soporte_id_seq'::regclass);


--
-- Name: ordenes_trabajo id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordenes_trabajo ALTER COLUMN id SET DEFAULT nextval('public.ordenes_trabajo_id_seq'::regclass);


--
-- Name: ot_actividades id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ot_actividades ALTER COLUMN id SET DEFAULT nextval('public.ot_actividades_id_seq'::regclass);


--
-- Name: pagos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagos ALTER COLUMN id SET DEFAULT nextval('public.pagos_id_seq'::regclass);


--
-- Name: reclamos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos ALTER COLUMN id SET DEFAULT nextval('public.reclamos_id_seq'::regclass);


--
-- Name: reclamos_fallas_masivas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos_fallas_masivas ALTER COLUMN id SET DEFAULT nextval('public.reclamos_fallas_masivas_id_seq'::regclass);


--
-- Name: reclamos_seguimiento id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos_seguimiento ALTER COLUMN id SET DEFAULT nextval('public.reclamos_seguimiento_id_seq'::regclass);


--
-- Name: roles id_rol; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id_rol SET DEFAULT nextval('public.roles_id_rol_seq'::regclass);


--
-- Name: servicios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios ALTER COLUMN id SET DEFAULT nextval('public.servicios_id_seq'::regclass);


--
-- Name: servicios_disponibles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios_disponibles ALTER COLUMN id SET DEFAULT nextval('public.servicios_disponibles_id_seq'::regclass);


--
-- Name: tecnicos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tecnicos ALTER COLUMN id SET DEFAULT nextval('public.tecnicos_id_seq'::regclass);


--
-- Name: tipos_problemas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_problemas ALTER COLUMN id SET DEFAULT nextval('public.tipos_problemas_id_seq'::regclass);


--
-- Name: trabajos_reparados id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajos_reparados ALTER COLUMN id SET DEFAULT nextval('public.trabajos_reparados_id_seq'::regclass);


--
-- Name: usuarios usuario_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN usuario_id SET DEFAULT nextval('public.usuarios_usuario_id_seq'::regclass);


--
-- Name: zonas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zonas ALTER COLUMN id SET DEFAULT nextval('public.zonas_id_seq'::regclass);


--
-- Name: auditorias_calidad auditorias_calidad_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditorias_calidad
    ADD CONSTRAINT auditorias_calidad_pkey PRIMARY KEY (id);


--
-- Name: codigos_falla codigos_falla_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_falla
    ADD CONSTRAINT codigos_falla_codigo_key UNIQUE (codigo);


--
-- Name: codigos_falla codigos_falla_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_falla
    ADD CONSTRAINT codigos_falla_pkey PRIMARY KEY (id);


--
-- Name: codigos_ivr_liberacion codigos_ivr_liberacion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_ivr_liberacion
    ADD CONSTRAINT codigos_ivr_liberacion_pkey PRIMARY KEY (id);


--
-- Name: codigos_ivr_liberacion codigos_ivr_liberacion_servicio_medio_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_ivr_liberacion
    ADD CONSTRAINT codigos_ivr_liberacion_servicio_medio_key UNIQUE (servicio, medio);


--
-- Name: codigos_registro_cliente codigos_registro_cliente_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_cliente
    ADD CONSTRAINT codigos_registro_cliente_codigo_key UNIQUE (codigo);


--
-- Name: codigos_registro_cliente codigos_registro_cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_cliente
    ADD CONSTRAINT codigos_registro_cliente_pkey PRIMARY KEY (id);


--
-- Name: codigos_registro_empleado codigos_registro_empleado_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_empleado
    ADD CONSTRAINT codigos_registro_empleado_codigo_key UNIQUE (codigo);


--
-- Name: codigos_registro_empleado codigos_registro_empleado_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_empleado
    ADD CONSTRAINT codigos_registro_empleado_pkey PRIMARY KEY (id);


--
-- Name: codigos_solucion codigos_solucion_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_solucion
    ADD CONSTRAINT codigos_solucion_codigo_key UNIQUE (codigo);


--
-- Name: codigos_solucion codigos_solucion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_solucion
    ADD CONSTRAINT codigos_solucion_pkey PRIMARY KEY (id);


--
-- Name: contratos contratos_numero_contrato_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_numero_contrato_key UNIQUE (numero_contrato);


--
-- Name: contratos contratos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_pkey PRIMARY KEY (id);


--
-- Name: cuentas_pago_tramites cuentas_pago_tramites_codigo_cuenta_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cuentas_pago_tramites
    ADD CONSTRAINT cuentas_pago_tramites_codigo_cuenta_key UNIQUE (codigo_cuenta);


--
-- Name: cuentas_pago_tramites cuentas_pago_tramites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cuentas_pago_tramites
    ADD CONSTRAINT cuentas_pago_tramites_pkey PRIMARY KEY (id);


--
-- Name: diagnosticos_remotos diagnosticos_remotos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnosticos_remotos
    ADD CONSTRAINT diagnosticos_remotos_pkey PRIMARY KEY (id);


--
-- Name: elementos_red elementos_red_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.elementos_red
    ADD CONSTRAINT elementos_red_codigo_key UNIQUE (codigo);


--
-- Name: elementos_red elementos_red_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.elementos_red
    ADD CONSTRAINT elementos_red_pkey PRIMARY KEY (id);


--
-- Name: empleados_soporte empleados_soporte_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.empleados_soporte
    ADD CONSTRAINT empleados_soporte_pkey PRIMARY KEY (id);


--
-- Name: facturas facturas_numero_factura_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_numero_factura_key UNIQUE (numero_factura);


--
-- Name: facturas facturas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_pkey PRIMARY KEY (id);


--
-- Name: fallas_masivas fallas_masivas_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallas_masivas
    ADD CONSTRAINT fallas_masivas_codigo_key UNIQUE (codigo);


--
-- Name: fallas_masivas fallas_masivas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallas_masivas
    ADD CONSTRAINT fallas_masivas_pkey PRIMARY KEY (id);


--
-- Name: feriados feriados_fecha_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feriados
    ADD CONSTRAINT feriados_fecha_key UNIQUE (fecha);


--
-- Name: feriados feriados_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feriados
    ADD CONSTRAINT feriados_pkey PRIMARY KEY (id);


--
-- Name: historial_zona historial_zona_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_zona
    ADD CONSTRAINT historial_zona_pkey PRIMARY KEY (id);


--
-- Name: notificaciones_enviadas notificaciones_enviadas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_enviadas
    ADD CONSTRAINT notificaciones_enviadas_pkey PRIMARY KEY (id);


--
-- Name: notificaciones_jefe notificaciones_jefe_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_jefe
    ADD CONSTRAINT notificaciones_jefe_pkey PRIMARY KEY (id);


--
-- Name: notificaciones_soporte notificaciones_soporte_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_soporte
    ADD CONSTRAINT notificaciones_soporte_pkey PRIMARY KEY (id);


--
-- Name: ordenes_trabajo ordenes_trabajo_numero_ot_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordenes_trabajo
    ADD CONSTRAINT ordenes_trabajo_numero_ot_key UNIQUE (numero_ot);


--
-- Name: ordenes_trabajo ordenes_trabajo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordenes_trabajo
    ADD CONSTRAINT ordenes_trabajo_pkey PRIMARY KEY (id);


--
-- Name: ot_actividades ot_actividades_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ot_actividades
    ADD CONSTRAINT ot_actividades_pkey PRIMARY KEY (id);


--
-- Name: pagos pagos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_pkey PRIMARY KEY (id);


--
-- Name: reclamos_fallas_masivas reclamos_fallas_masivas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos_fallas_masivas
    ADD CONSTRAINT reclamos_fallas_masivas_pkey PRIMARY KEY (id);


--
-- Name: reclamos_fallas_masivas reclamos_fallas_masivas_reclamo_id_falla_masiva_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos_fallas_masivas
    ADD CONSTRAINT reclamos_fallas_masivas_reclamo_id_falla_masiva_id_key UNIQUE (reclamo_id, falla_masiva_id);


--
-- Name: reclamos reclamos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos
    ADD CONSTRAINT reclamos_pkey PRIMARY KEY (id);


--
-- Name: reclamos_seguimiento reclamos_seguimiento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos_seguimiento
    ADD CONSTRAINT reclamos_seguimiento_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id_rol);


--
-- Name: roles roles_rol_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_rol_key UNIQUE (rol);


--
-- Name: servicios_disponibles servicios_disponibles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios_disponibles
    ADD CONSTRAINT servicios_disponibles_pkey PRIMARY KEY (id);


--
-- Name: servicios servicios_numero_servicio_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios
    ADD CONSTRAINT servicios_numero_servicio_key UNIQUE (numero_servicio);


--
-- Name: servicios servicios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios
    ADD CONSTRAINT servicios_pkey PRIMARY KEY (id);


--
-- Name: tecnicos tecnicos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tecnicos
    ADD CONSTRAINT tecnicos_pkey PRIMARY KEY (id);


--
-- Name: tipos_problemas tipos_problemas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_problemas
    ADD CONSTRAINT tipos_problemas_pkey PRIMARY KEY (id);


--
-- Name: trabajos_reparados trabajos_reparados_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajos_reparados
    ADD CONSTRAINT trabajos_reparados_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_correo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_correo_key UNIQUE (correo);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (usuario_id);


--
-- Name: zonas zonas_nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zonas
    ADD CONSTRAINT zonas_nombre_key UNIQUE (nombre);


--
-- Name: zonas zonas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zonas
    ADD CONSTRAINT zonas_pkey PRIMARY KEY (id);


--
-- Name: idx_auditorias_auditor; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auditorias_auditor ON public.auditorias_calidad USING btree (auditor_id);


--
-- Name: idx_auditorias_reclamo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auditorias_reclamo ON public.auditorias_calidad USING btree (reclamo_id);


--
-- Name: idx_codigos_cliente_usado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_codigos_cliente_usado ON public.codigos_registro_cliente USING btree (usado);


--
-- Name: idx_codigos_empleado_rol; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_codigos_empleado_rol ON public.codigos_registro_empleado USING btree (rol);


--
-- Name: idx_codigos_registro_empleado_id_rol; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_codigos_registro_empleado_id_rol ON public.codigos_registro_empleado USING btree (id_rol);


--
-- Name: idx_contratos_numero; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_contratos_numero ON public.contratos USING btree (numero_contrato);


--
-- Name: idx_contratos_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_contratos_usuario ON public.contratos USING btree (usuario_id);


--
-- Name: idx_diagnosticos_reclamo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_diagnosticos_reclamo ON public.diagnosticos_remotos USING btree (reclamo_id);


--
-- Name: idx_fallas_masivas_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fallas_masivas_estado ON public.fallas_masivas USING btree (estado);


--
-- Name: idx_historial_zona_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_historial_zona_usuario ON public.historial_zona USING btree (usuario_id);


--
-- Name: idx_notif_jefe_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notif_jefe_usuario ON public.notificaciones_jefe USING btree (usuario_id);


--
-- Name: idx_pagos_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pagos_usuario ON public.pagos USING btree (usuario_id);


--
-- Name: idx_reclamos_asignado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_asignado ON public.reclamos USING btree (asignado_a);


--
-- Name: idx_reclamos_codigo_falla; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_codigo_falla ON public.reclamos USING btree (codigo_falla_id);


--
-- Name: idx_reclamos_escalado_a; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_escalado_a ON public.reclamos USING btree (escalado_a);


--
-- Name: idx_reclamos_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_estado ON public.reclamos USING btree (estado);


--
-- Name: idx_reclamos_estado_cuenta; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_estado_cuenta ON public.reclamos USING btree (estado_cuenta);


--
-- Name: idx_reclamos_falla_masiva; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_falla_masiva ON public.reclamos USING btree (falla_masiva_id);


--
-- Name: idx_reclamos_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_fecha ON public.reclamos USING btree (fecha_creacion);


--
-- Name: idx_reclamos_instancia; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_instancia ON public.reclamos USING btree (instancia);


--
-- Name: idx_reclamos_medio_fisico; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_medio_fisico ON public.reclamos USING btree (medio_fisico);


--
-- Name: idx_reclamos_prioridad; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_prioridad ON public.reclamos USING btree (prioridad);


--
-- Name: idx_reclamos_problema; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_problema ON public.reclamos USING btree (problema_especifico);


--
-- Name: idx_reclamos_servicio; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_servicio ON public.reclamos USING btree (servicio_afectado);


--
-- Name: idx_reclamos_turno_nocturno; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_turno_nocturno ON public.reclamos USING btree (es_turno_nocturno);


--
-- Name: idx_reclamos_ubicacion; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_ubicacion ON public.reclamos USING btree (ubicacion_cliente);


--
-- Name: idx_reclamos_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reclamos_usuario ON public.reclamos USING btree (usuario_id);


--
-- Name: idx_rfm_falla; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_rfm_falla ON public.reclamos_fallas_masivas USING btree (falla_masiva_id);


--
-- Name: idx_rfm_reclamo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_rfm_reclamo ON public.reclamos_fallas_masivas USING btree (reclamo_id);


--
-- Name: idx_tecnicos_instancia; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tecnicos_instancia ON public.tecnicos USING btree (instancia_tecnico);


--
-- Name: idx_tecnicos_servicio_medio; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tecnicos_servicio_medio ON public.tecnicos USING btree (servicio_tecnico, medio_tecnico);


--
-- Name: idx_tecnicos_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tecnicos_tipo ON public.tecnicos USING btree (tipo_tecnico);


--
-- Name: idx_trabajos_reparados_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_trabajos_reparados_fecha ON public.trabajos_reparados USING btree (fecha_fin);


--
-- Name: idx_trabajos_reparados_instancia; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_trabajos_reparados_instancia ON public.trabajos_reparados USING btree (instancia);


--
-- Name: idx_trabajos_reparados_tecnico; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_trabajos_reparados_tecnico ON public.trabajos_reparados USING btree (tecnico_id);


--
-- Name: auditorias_calidad auditorias_calidad_auditor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditorias_calidad
    ADD CONSTRAINT auditorias_calidad_auditor_id_fkey FOREIGN KEY (auditor_id) REFERENCES public.usuarios(usuario_id);


--
-- Name: auditorias_calidad auditorias_calidad_reclamo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditorias_calidad
    ADD CONSTRAINT auditorias_calidad_reclamo_id_fkey FOREIGN KEY (reclamo_id) REFERENCES public.reclamos(id) ON DELETE CASCADE;


--
-- Name: codigos_registro_cliente codigos_registro_cliente_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_cliente
    ADD CONSTRAINT codigos_registro_cliente_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id);


--
-- Name: codigos_registro_empleado codigos_registro_empleado_id_rol_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_empleado
    ADD CONSTRAINT codigos_registro_empleado_id_rol_fkey FOREIGN KEY (id_rol) REFERENCES public.roles(id_rol);


--
-- Name: codigos_registro_empleado codigos_registro_empleado_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codigos_registro_empleado
    ADD CONSTRAINT codigos_registro_empleado_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id);


--
-- Name: contratos contratos_servicio_origen_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_servicio_origen_id_fkey FOREIGN KEY (servicio_origen_id) REFERENCES public.servicios(id);


--
-- Name: contratos contratos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id) ON DELETE CASCADE;


--
-- Name: contratos contratos_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id);


--
-- Name: diagnosticos_remotos diagnosticos_remotos_codigo_falla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnosticos_remotos
    ADD CONSTRAINT diagnosticos_remotos_codigo_falla_id_fkey FOREIGN KEY (codigo_falla_id) REFERENCES public.codigos_falla(id);


--
-- Name: diagnosticos_remotos diagnosticos_remotos_elemento_afectado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnosticos_remotos
    ADD CONSTRAINT diagnosticos_remotos_elemento_afectado_id_fkey FOREIGN KEY (elemento_afectado_id) REFERENCES public.elementos_red(id);


--
-- Name: diagnosticos_remotos diagnosticos_remotos_operador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnosticos_remotos
    ADD CONSTRAINT diagnosticos_remotos_operador_id_fkey FOREIGN KEY (operador_id) REFERENCES public.usuarios(usuario_id);


--
-- Name: diagnosticos_remotos diagnosticos_remotos_reclamo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diagnosticos_remotos
    ADD CONSTRAINT diagnosticos_remotos_reclamo_id_fkey FOREIGN KEY (reclamo_id) REFERENCES public.reclamos(id) ON DELETE CASCADE;


--
-- Name: empleados_soporte empleados_soporte_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.empleados_soporte
    ADD CONSTRAINT empleados_soporte_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id);


--
-- Name: facturas facturas_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id) ON DELETE CASCADE;


--
-- Name: fallas_masivas fallas_masivas_codigo_falla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallas_masivas
    ADD CONSTRAINT fallas_masivas_codigo_falla_id_fkey FOREIGN KEY (codigo_falla_id) REFERENCES public.codigos_falla(id);


--
-- Name: fallas_masivas fallas_masivas_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallas_masivas
    ADD CONSTRAINT fallas_masivas_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(usuario_id);


--
-- Name: fallas_masivas fallas_masivas_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fallas_masivas
    ADD CONSTRAINT fallas_masivas_responsable_id_fkey FOREIGN KEY (responsable_id) REFERENCES public.usuarios(usuario_id);


--
-- Name: reclamos fk_reclamos_falla_masiva; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos
    ADD CONSTRAINT fk_reclamos_falla_masiva FOREIGN KEY (falla_masiva_id) REFERENCES public.fallas_masivas(id);


--
-- Name: usuarios fk_roles; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_roles FOREIGN KEY (id_rol) REFERENCES public.roles(id_rol);


--
-- Name: historial_zona historial_zona_modificado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_zona
    ADD CONSTRAINT historial_zona_modificado_por_fkey FOREIGN KEY (modificado_por) REFERENCES public.usuarios(usuario_id);


--
-- Name: historial_zona historial_zona_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_zona
    ADD CONSTRAINT historial_zona_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id) ON DELETE CASCADE;


--
-- Name: historial_zona historial_zona_zona_anterior_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_zona
    ADD CONSTRAINT historial_zona_zona_anterior_id_fkey FOREIGN KEY (zona_anterior_id) REFERENCES public.zonas(id);


--
-- Name: historial_zona historial_zona_zona_nueva_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_zona
    ADD CONSTRAINT historial_zona_zona_nueva_id_fkey FOREIGN KEY (zona_nueva_id) REFERENCES public.zonas(id);


--
-- Name: notificaciones_enviadas notificaciones_enviadas_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_enviadas
    ADD CONSTRAINT notificaciones_enviadas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id);


--
-- Name: notificaciones_jefe notificaciones_jefe_reclamo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_jefe
    ADD CONSTRAINT notificaciones_jefe_reclamo_id_fkey FOREIGN KEY (reclamo_id) REFERENCES public.reclamos(id) ON DELETE CASCADE;


--
-- Name: notificaciones_jefe notificaciones_jefe_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_jefe
    ADD CONSTRAINT notificaciones_jefe_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id) ON DELETE CASCADE;


--
-- Name: notificaciones_soporte notificaciones_soporte_empleado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones_soporte
    ADD CONSTRAINT notificaciones_soporte_empleado_id_fkey FOREIGN KEY (empleado_id) REFERENCES public.empleados_soporte(id);


--
-- Name: ordenes_trabajo ordenes_trabajo_codigo_solucion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordenes_trabajo
    ADD CONSTRAINT ordenes_trabajo_codigo_solucion_id_fkey FOREIGN KEY (codigo_solucion_id) REFERENCES public.codigos_solucion(id);


--
-- Name: ordenes_trabajo ordenes_trabajo_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordenes_trabajo
    ADD CONSTRAINT ordenes_trabajo_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(usuario_id);


--
-- Name: ordenes_trabajo ordenes_trabajo_reclamo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordenes_trabajo
    ADD CONSTRAINT ordenes_trabajo_reclamo_id_fkey FOREIGN KEY (reclamo_id) REFERENCES public.reclamos(id);


--
-- Name: ordenes_trabajo ordenes_trabajo_tecnico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordenes_trabajo
    ADD CONSTRAINT ordenes_trabajo_tecnico_id_fkey FOREIGN KEY (tecnico_id) REFERENCES public.tecnicos(id);


--
-- Name: ordenes_trabajo ordenes_trabajo_usuario_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordenes_trabajo
    ADD CONSTRAINT ordenes_trabajo_usuario_cliente_id_fkey FOREIGN KEY (usuario_cliente_id) REFERENCES public.usuarios(usuario_id);


--
-- Name: ot_actividades ot_actividades_ot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ot_actividades
    ADD CONSTRAINT ot_actividades_ot_id_fkey FOREIGN KEY (ot_id) REFERENCES public.ordenes_trabajo(id) ON DELETE CASCADE;


--
-- Name: ot_actividades ot_actividades_tecnico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ot_actividades
    ADD CONSTRAINT ot_actividades_tecnico_id_fkey FOREIGN KEY (tecnico_id) REFERENCES public.tecnicos(id);


--
-- Name: pagos pagos_factura_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_factura_id_fkey FOREIGN KEY (factura_id) REFERENCES public.facturas(id);


--
-- Name: pagos pagos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id) ON DELETE CASCADE;


--
-- Name: reclamos reclamos_asignado_a_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos
    ADD CONSTRAINT reclamos_asignado_a_fkey FOREIGN KEY (asignado_a) REFERENCES public.tecnicos(id) ON DELETE SET NULL;


--
-- Name: reclamos reclamos_codigo_falla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos
    ADD CONSTRAINT reclamos_codigo_falla_id_fkey FOREIGN KEY (codigo_falla_id) REFERENCES public.codigos_falla(id);


--
-- Name: reclamos reclamos_elemento_afectado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos
    ADD CONSTRAINT reclamos_elemento_afectado_id_fkey FOREIGN KEY (elemento_afectado_id) REFERENCES public.elementos_red(id);


--
-- Name: reclamos_fallas_masivas reclamos_fallas_masivas_falla_masiva_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos_fallas_masivas
    ADD CONSTRAINT reclamos_fallas_masivas_falla_masiva_id_fkey FOREIGN KEY (falla_masiva_id) REFERENCES public.fallas_masivas(id) ON DELETE CASCADE;


--
-- Name: reclamos_fallas_masivas reclamos_fallas_masivas_reclamo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos_fallas_masivas
    ADD CONSTRAINT reclamos_fallas_masivas_reclamo_id_fkey FOREIGN KEY (reclamo_id) REFERENCES public.reclamos(id) ON DELETE CASCADE;


--
-- Name: reclamos reclamos_registrado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos
    ADD CONSTRAINT reclamos_registrado_por_fkey FOREIGN KEY (registrado_por) REFERENCES public.usuarios(usuario_id);


--
-- Name: reclamos_seguimiento reclamos_seguimiento_empleado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos_seguimiento
    ADD CONSTRAINT reclamos_seguimiento_empleado_id_fkey FOREIGN KEY (empleado_id) REFERENCES public.empleados_soporte(id);


--
-- Name: reclamos reclamos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reclamos
    ADD CONSTRAINT reclamos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id) ON DELETE CASCADE;


--
-- Name: servicios servicios_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios
    ADD CONSTRAINT servicios_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id) ON DELETE CASCADE;


--
-- Name: tecnicos tecnicos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tecnicos
    ADD CONSTRAINT tecnicos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(usuario_id) ON DELETE CASCADE;


--
-- Name: tecnicos tecnicos_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tecnicos
    ADD CONSTRAINT tecnicos_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id);


--
-- Name: tipos_problemas tipos_problemas_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_problemas
    ADD CONSTRAINT tipos_problemas_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicios_disponibles(id);


--
-- Name: trabajos_reparados trabajos_reparados_ot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajos_reparados
    ADD CONSTRAINT trabajos_reparados_ot_id_fkey FOREIGN KEY (ot_id) REFERENCES public.ordenes_trabajo(id);


--
-- Name: trabajos_reparados trabajos_reparados_reclamo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajos_reparados
    ADD CONSTRAINT trabajos_reparados_reclamo_id_fkey FOREIGN KEY (reclamo_id) REFERENCES public.reclamos(id);


--
-- Name: trabajos_reparados trabajos_reparados_tecnico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trabajos_reparados
    ADD CONSTRAINT trabajos_reparados_tecnico_id_fkey FOREIGN KEY (tecnico_id) REFERENCES public.tecnicos(id);


--
-- Name: usuarios usuarios_zona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_zona_id_fkey FOREIGN KEY (zona_id) REFERENCES public.zonas(id);


--
-- PostgreSQL database dump complete
--

