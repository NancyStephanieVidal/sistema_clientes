// Script para el formulario de captura de clientes
document.addEventListener('DOMContentLoaded', function() {
    // Validación en tiempo real del formulario
    const formulario = document.getElementById('clienteForm');
    
    // ========== INTEGRACIÓN API DE RECOMENDACIÓN ==========
    // Elementos para la recomendación de sucursal
    const btnRecomendar = document.getElementById('btnRecomendar');
    const domicilioInput = document.getElementById('domicilio');
    const sucursalSelect = document.getElementById('sucursal');
    
    // Crear botón de recomendación si no existe
    if (domicilioInput && sucursalSelect && !btnRecomendar) {
        crearBotonRecomendacion();
    }
    
    // Inicializar funcionalidad de recomendación
    inicializarRecomendacion();
    
    if (formulario) {
        const inputs = formulario.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Validación al perder el foco
            input.addEventListener('blur', function() {
                validarCampo(this);
            });
            
            // Validación al escribir (solo para campos requeridos)
            if (input.hasAttribute('required')) {
                input.addEventListener('input', function() {
                    validarCampoEnTiempoReal(this);
                });
            }
        });
        
        // Validación antes de enviar
        formulario.addEventListener('submit', function(e) {
            if (!validarFormularioCompleto()) {
                e.preventDefault();
                mostrarMensajeError('Por favor, complete todos los campos obligatorios correctamente.');
            }
        });
    }
    
    // ========== FUNCIONES DE RECOMENDACIÓN ==========
    function crearBotonRecomendacion() {
        // Crear contenedor para el botón de recomendación
        const domicilioGroup = domicilioInput.closest('.form-group');
        if (domicilioGroup) {
            const recomendacionContainer = document.createElement('div');
            recomendacionContainer.className = 'recomendacion-container';
            recomendacionContainer.style.marginTop = '15px';
            recomendacionContainer.style.padding = '15px';
            recomendacionContainer.style.backgroundColor = '#f8f9fa';
            recomendacionContainer.style.borderRadius = '8px';
            recomendacionContainer.style.border = '1px solid #dee2e6';
            
            const button = document.createElement('button');
            button.type = 'button';
            button.id = 'btnRecomendar';
            button.className = 'btn btn-info';
            button.innerHTML = '<i class="fas fa-map-marker-alt"></i> Recomendar Sucursal Más Cercana';
            button.style.display = 'flex';
            button.style.alignItems = 'center';
            button.style.gap = '8px';
            button.style.padding = '10px 15px';
            button.style.borderRadius = '6px';
            button.style.border = 'none';
            button.style.backgroundColor = '#17a2b8';
            button.style.color = 'white';
            button.style.cursor = 'pointer';
            button.style.fontSize = '14px';
            button.style.transition = 'all 0.3s ease';
            
            button.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#138496';
                this.style.transform = 'translateY(-2px)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '#17a2b8';
                this.style.transform = 'translateY(0)';
            });
            
            const resultadoDiv = document.createElement('div');
            resultadoDiv.id = 'recomendacionResultado';
            resultadoDiv.style.display = 'none';
            resultadoDiv.style.marginTop = '15px';
            resultadoDiv.style.padding = '15px';
            resultadoDiv.style.backgroundColor = '#e7f3ff';
            resultadoDiv.style.borderRadius = '5px';
            resultadoDiv.style.borderLeft = '4px solid #007bff';
            
            resultadoDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <i class="fas fa-lightbulb" style="color: #007bff; font-size: 18px;"></i>
                    <h4 style="margin: 0; color: #0056b3; font-size: 16px;">Sugerencia de Sucursal</h4>
                </div>
                <div style="margin-bottom: 8px;">
                    <strong><i class="fas fa-store"></i> Sucursal recomendada:</strong> 
                    <span id="sucursalRecomendada" style="color: #28a745; font-weight: bold;"></span>
                </div>
                <div style="margin-bottom: 8px;">
                    <strong><i class="fas fa-map"></i> Distancia aproximada:</strong> 
                    <span id="distanciaRecomendada"></span>
                </div>
                <div>
                    <strong><i class="fas fa-info-circle"></i> Razón:</strong> 
                    <span id="razonRecomendacion" style="font-style: italic;"></span>
                </div>
            `;
            
            recomendacionContainer.appendChild(button);
            recomendacionContainer.appendChild(resultadoDiv);
            domicilioGroup.appendChild(recomendacionContainer);
        }
    }
    
    function inicializarRecomendacion() {
        const btn = document.getElementById('btnRecomendar');
        const domicilio = document.getElementById('domicilio');
        const sucursal = document.getElementById('sucursal');
        
        if (btn && domicilio && sucursal) {
            btn.addEventListener('click', async function() {
                const domicilioValor = domicilio.value.trim();
                
                if (domicilioValor.length < 5) {
                    mostrarMensajeError('Por favor, ingrese un domicilio válido (mínimo 5 caracteres) para recomendar sucursal.');
                    return;
                }
                
                // Mostrar carga
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculando...';
                btn.disabled = true;
                
                try {
                    // Llamar a la API de FastAPI
                    const response = await fetch(
                        `http://localhost:8000/api/recomendacion/domicilio?domicilio=${encodeURIComponent(domicilioValor)}`
                    );
                    
                    if (!response.ok) {
                        throw new Error(`Error HTTP: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    // Mostrar recomendación
                    document.getElementById('sucursalRecomendada').textContent = data.sucursal_recomendada;
                    document.getElementById('distanciaRecomendada').textContent = 
                        typeof data.distancia_km === 'number' ? 
                        `${data.distancia_km} km` : 
                        data.distancia_km;
                    document.getElementById('razonRecomendacion').textContent = data.razon;
                    
                    const resultadoDiv = document.getElementById('recomendacionResultado');
                    resultadoDiv.style.display = 'block';
                    
                    // Seleccionar automáticamente la sucursal recomendada
                    if (sucursal) {
                        for (let i = 0; i < sucursal.options.length; i++) {
                            if (sucursal.options[i].value === data.sucursal_recomendada) {
                                sucursal.selectedIndex = i;
                                sucursal.style.borderColor = '#28a745';
                                
                                // Mostrar notificación de éxito
                                mostrarNotificacion(`Sucursal "${data.sucursal_recomendada}" seleccionada automáticamente`, 'success');
                                break;
                            }
                        }
                    }
                    
                    // Efecto visual
                    resultadoDiv.style.animation = 'fadeIn 0.5s ease';
                    
                } catch (error) {
                    console.error('Error al obtener recomendación:', error);
                    
                    // Mostrar mensaje de error amigable
                    const resultadoDiv = document.getElementById('recomendacionResultado');
                    resultadoDiv.innerHTML = `
                        <div style="color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;">
                            <i class="fas fa-exclamation-triangle"></i>
                            <strong> Error:</strong> No se pudo obtener recomendación. 
                            <br><small>Asegúrate de que la API esté corriendo en http://localhost:8000</small>
                        </div>
                    `;
                    resultadoDiv.style.display = 'block';
                    
                } finally {
                    // Restaurar botón
                    btn.innerHTML = '<i class="fas fa-map-marker-alt"></i> Recomendar Sucursal Más Cercana';
                    btn.disabled = false;
                }
            });
        }
    }
    
    function mostrarNotificacion(mensaje, tipo = 'info') {
        // Crear notificación flotante
        const notificacion = document.createElement('div');
        notificacion.className = 'notificacion-flotante';
        notificacion.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${tipo === 'success' ? 'check-circle' : 'info-circle'}" 
                   style="color: ${tipo === 'success' ? '#28a745' : '#17a2b8'}"></i>
                <span>${mensaje}</span>
            </div>
        `;
        
        // Estilos
        notificacion.style.position = 'fixed';
        notificacion.style.top = '20px';
        notificacion.style.right = '20px';
        notificacion.style.padding = '15px 20px';
        notificacion.style.backgroundColor = tipo === 'success' ? '#d4edda' : '#d1ecf1';
        notificacion.style.color = tipo === 'success' ? '#155724' : '#0c5460';
        notificacion.style.border = `1px solid ${tipo === 'success' ? '#c3e6cb' : '#bee5eb'}`;
        notificacion.style.borderRadius = '8px';
        notificacion.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
        notificacion.style.zIndex = '1000';
        notificacion.style.animation = 'slideIn 0.3s ease';
        
        document.body.appendChild(notificacion);
        
        // Auto-eliminar después de 5 segundos
        setTimeout(() => {
            notificacion.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notificacion.remove(), 300);
        }, 5000);
    }
    
    // ========== FUNCIONES DE VALIDACIÓN EXISTENTES ==========
    function validarCampo(campo) {
        const valor = campo.value.trim();
        const grupo = campo.closest('.form-group');
        
        // Limpiar mensajes anteriores
        limpiarErrores(grupo);
        
        // Validar campo requerido
        if (campo.hasAttribute('required') && valor === '') {
            mostrarError(grupo, 'Este campo es obligatorio');
            return false;
        }
        
        // Validaciones específicas por tipo
        switch(campo.type) {
            case 'email':
                if (valor && !validarEmail(valor)) {
                    mostrarError(grupo, 'Ingrese un correo electrónico válido');
                    return false;
                }
                break;
                
            case 'text':
                if (campo.hasAttribute('minlength')) {
                    const minLength = parseInt(campo.getAttribute('minlength'));
                    if (valor.length < minLength) {
                        mostrarError(grupo, `Mínimo ${minLength} caracteres`);
                        return false;
                    }
                }
                break;
                
            case 'textarea':
                if (campo.id === 'domicilio' && valor.length > 0) {
                    // Si hay domicilio, habilitar botón de recomendación
                    const btnRecomendar = document.getElementById('btnRecomendar');
                    if (btnRecomendar && valor.length >= 5) {
                        btnRecomendar.disabled = false;
                    }
                }
                break;
        }
        
        // Si pasa todas las validaciones
        marcarValido(grupo);
        return true;
    }
    
    function validarCampoEnTiempoReal(campo) {
        const valor = campo.value.trim();
        const grupo = campo.closest('.form-group');
        
        if (valor === '') {
            limpiarEstado(grupo);
            return;
        }
        
        validarCampo(campo);
    }
    
    function validarFormularioCompleto() {
        let esValido = true;
        const camposRequeridos = formulario.querySelectorAll('[required]');
        
        camposRequeridos.forEach(campo => {
            if (!validarCampo(campo)) {
                esValido = false;
            }
        });
        
        return esValido;
    }
    
    // Funciones auxiliares
    function validarEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }
    
    function mostrarError(grupo, mensaje) {
        // Eliminar mensajes previos
        limpiarErrores(grupo);
        
        // Crear elemento de error
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${mensaje}`;
        errorElement.style.color = '#e74c3c';
        errorElement.style.fontSize = '14px';
        errorElement.style.marginTop = '5px';
        errorElement.style.display = 'flex';
        errorElement.style.alignItems = 'center';
        errorElement.style.gap = '8px';
        
        grupo.appendChild(errorElement);
        
        // Marcar campo como inválido
        const input = grupo.querySelector('input, select, textarea');
        input.style.borderColor = '#e74c3c';
    }
    
    function limpiarErrores(grupo) {
        const errores = grupo.querySelectorAll('.error-message');
        errores.forEach(error => error.remove());
    }
    
    function limpiarEstado(grupo) {
        const input = grupo.querySelector('input, select, textarea');
        input.style.borderColor = '#ddd';
        limpiarErrores(grupo);
    }
    
    function marcarValido(grupo) {
        const input = grupo.querySelector('input, select, textarea');
        input.style.borderColor = '#2ecc71';
    }
    
    function mostrarMensajeError(mensaje) {
        // Crear o mostrar mensaje de error global
        let errorGlobal = document.querySelector('.error-global');
        
        if (!errorGlobal) {
            errorGlobal = document.createElement('div');
            errorGlobal.className = 'error-global';
            errorGlobal.style.backgroundColor = '#f8d7da';
            errorGlobal.style.color = '#721c24';
            errorGlobal.style.padding = '15px';
            errorGlobal.style.borderRadius = '8px';
            errorGlobal.style.marginBottom = '20px';
            errorGlobal.style.border = '1px solid #f5c6cb';
            errorGlobal.style.display = 'flex';
            errorGlobal.style.alignItems = 'center';
            errorGlobal.style.gap = '10px';
            
            const formHeader = document.querySelector('.form-header');
            if (formHeader) {
                formHeader.parentNode.insertBefore(errorGlobal, formHeader.nextSibling);
            }
        }
        
        errorGlobal.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${mensaje}`;
    }
    
    // Efectos visuales para la tabla de clientes
    const tableRows = document.querySelectorAll('.clients-table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
            this.style.transition = 'transform 0.2s ease';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
    
    // Animación para los botones
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.boxShadow = '0 6px 12px rgba(0,0,0,0.15)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });
    
    // ========== AÑADIR ANIMACIONES CSS ==========
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .recomendacion-container {
            animation: fadeIn 0.5s ease;
        }
        
        #recomendacionResultado {
            animation: fadeIn 0.5s ease;
        }
    `;
    document.head.appendChild(style);
});

// Función para probar la API desde consola (para desarrollo)
function probarAPI() {
    console.log('🔧 Pruebas de API disponibles:');
    console.log('1. fetch("http://localhost:8000/api/clientes").then(r => r.json())');
    console.log('2. fetch("http://localhost:8000/api/motocicletas?marca=KTM").then(r => r.json())');
    console.log('3. fetch("http://localhost:8000/api/recomendacion/domicilio?domicilio=Coyoacan").then(r => r.json())');
    console.log('📚 Documentación: http://localhost:8000/docs');
}