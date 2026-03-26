-- SQL Server schema for Autodesk License Manager
-- Database: SIG_DESARROLLO

-- Crear tabla users (administradores del sistema)
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(120) NOT NULL,
    email NVARCHAR(120) NOT NULL UNIQUE,
    hashed_password NVARCHAR(255) NOT NULL,
    role NVARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

-- Crear tabla software (catalogo de productos)
CREATE TABLE software (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL UNIQUE,
    vendor NVARCHAR(100) NOT NULL DEFAULT 'Autodesk'
);

-- Crear tabla licenses (registro de licencias con estructura del Excel)
CREATE TABLE licenses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    cedula NVARCHAR(20) NOT NULL UNIQUE,
    nombre NVARCHAR(150) NOT NULL,
    cargo NVARCHAR(100) NULL,
    proyecto NVARCHAR(150) NULL,
    software_id INT NOT NULL,
    correos_personales NVARCHAR(200) NULL,
    email_enviado_fecha DATE NULL,
    habilitacion_licencia_fecha DATE NULL,
    vencimiento_licencia_fecha DATE NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'Activa',
    verificacion_cedula BIT NOT NULL DEFAULT 0,
    verificacion_licencia BIT NOT NULL DEFAULT 0,
    verificacion_nomina BIT NOT NULL DEFAULT 0,
    observaciones NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_licenses_software FOREIGN KEY (software_id) REFERENCES software(id)
);

-- Crear tabla requests (solicitudes de nuevas licencias)
CREATE TABLE requests (
    id INT IDENTITY(1,1) PRIMARY KEY,
    request_type NVARCHAR(30) NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'Pendiente',
    user_id INT NOT NULL,
    software_id INT NOT NULL,
    cedula NVARCHAR(20) NULL,
    proyecto NVARCHAR(120) NOT NULL,
    justification NVARCHAR(MAX) NOT NULL,
    required_date DATE NOT NULL,
    payment_method NVARCHAR(80) NULL,
    contact_info NVARCHAR(180) NULL,
    process_owner NVARCHAR(120) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_requests_users FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT FK_requests_software FOREIGN KEY (software_id) REFERENCES software(id)
);

-- Crear tabla audit_logs (registro de cambios)
CREATE TABLE audit_logs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    action NVARCHAR(120) NOT NULL,
    entity NVARCHAR(80) NOT NULL,
    entity_id NVARCHAR(80) NOT NULL,
    details NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_audit_logs_users FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Crear indices para optimizacion
CREATE INDEX IX_users_email ON users(email);
CREATE INDEX IX_licenses_cedula ON licenses(cedula);
CREATE INDEX IX_licenses_vencimiento ON licenses(vencimiento_licencia_fecha);
CREATE INDEX IX_licenses_status ON licenses(status);
CREATE INDEX IX_requests_status ON requests(status);
CREATE INDEX IX_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IX_audit_logs_user_id ON audit_logs(user_id);
