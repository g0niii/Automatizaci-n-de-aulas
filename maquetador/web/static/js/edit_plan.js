/**
 * edit_plan.js - Cliente para editar planes de maquetación
 *
 * Validación cliente:
 *   - Título no vacío
 *   - Tipo en lista válida
 *   - Al menos un item por módulo
 *   - Archivo/sección consistentes
 *
 * Envío: POST /api/plan/<plan_id>/guardar
 */

class EditPlanForm {
  constructor(formSelector, planId) {
    this.form = document.querySelector(formSelector);
    this.planId = planId;
    this.tiposValidos = ['pagina', 'video', 'foro', 'tarea', 'evaluacion'];

    if (this.form) {
      this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }
  }

  /**
   * Valida que el título no esté vacío.
   */
  validarTitulo(titulo) {
    const trimmed = titulo.trim();
    return {
      valido: trimmed.length > 0,
      error: !trimmed.length ? 'El título no puede estar vacío' : ''
    };
  }

  /**
   * Valida que el tipo esté en la lista de tipos válidos.
   */
  validarTipo(tipo) {
    return {
      valido: this.tiposValidos.includes(tipo),
      error: !this.tiposValidos.includes(tipo)
        ? `Tipo inválido: ${tipo}. Válidos: ${this.tiposValidos.join(', ')}`
        : ''
    };
  }

  /**
   * Valida que el módulo tenga al menos un item.
   */
  validarModuloTieneItems(modulo) {
    return {
      valido: modulo.items.length > 0,
      error: modulo.items.length === 0
        ? `Módulo ${modulo.numero} no tiene items`
        : ''
    };
  }

  /**
   * Construye el plan editado desde el formulario.
   * Retorna { planEditado, errores }
   */
  construirPlan() {
    const errores = [];

    const planEditado = {
      nombre: document.getElementById('nombre').value,
      codigo: document.getElementById('codigo').value,
      tema: document.getElementById('tema').value,
      docentes: [],
      items_inicio: [],
      modulos: [],
      afi: [],
      issues: []
    };

    // Validar nombre no vacío
    const valNombre = this.validarTitulo(planEditado.nombre);
    if (!valNombre.valido) {
      errores.push(valNombre.error);
    }

    // Recorrer módulos
    document.querySelectorAll('.modulo-block').forEach((modBlock, modIdx) => {
      const modulo = {
        numero: modIdx + 1,
        titulo: modBlock.querySelector('.modulo-header h4')
          .textContent.replace(/Módulo \d+: /, ''),
        items: []
      };

      // Recorrer items del módulo
      modBlock.querySelectorAll('.item-block').forEach((itemBlock, itemIdx) => {
        const titulo = itemBlock.querySelector('.item-titulo').value;
        const tipo = itemBlock.querySelector('.item-tipo').value;
        const archivo = itemBlock.querySelector('.item-archivo').value;
        const seccion = itemBlock.querySelector('.item-seccion').value;

        // Validar título
        const valTit = this.validarTitulo(titulo);
        if (!valTit.valido) {
          errores.push(`Módulo ${modulo.numero}, Item ${itemIdx + 1}: ${valTit.error}`);
        }

        // Validar tipo
        const valTip = this.validarTipo(tipo);
        if (!valTip.valido) {
          errores.push(`Módulo ${modulo.numero}, Item ${itemIdx + 1}: ${valTip.error}`);
        }

        const item = {
          titulo: titulo,
          tipo: tipo,
          orden: itemIdx + 1,
          fuente: {
            archivo: archivo || null,
            seccion: seccion || null,
            confianza: 0.95,
            tiene_html: false
          },
          estado_planilla: 'Obligatorio',
          comentarios_asesor: '',
          detalle: {},
          issues: []
        };
        modulo.items.push(item);
      });

      // Validar módulo tiene items
      const valMod = this.validarModuloTieneItems(modulo);
      if (!valMod.valido) {
        errores.push(valMod.error);
      }

      planEditado.modulos.push(modulo);
    });

    return { planEditado, errores };
  }

  /**
   * Maneja el envío del formulario.
   */
  async handleSubmit(e) {
    e.preventDefault();

    const { planEditado, errores } = this.construirPlan();

    // Si hay errores de validación, mostrar y no enviar
    if (errores.length > 0) {
      this.mostrarError('Validación fallida:\n\n' + errores.join('\n'));
      return;
    }

    // Mostrar spinner de carga
    const btnGuardar = document.getElementById('btn-guardar');
    const textoOriginal = btnGuardar.textContent;
    btnGuardar.textContent = '⏳ Guardando...';
    btnGuardar.disabled = true;

    try {
      const response = await fetch(`/api/plan/${this.planId}/guardar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: planEditado })
      });

      const resultado = await response.json();

      if (resultado.exito) {
        this.mostrarExito('✅ Cambios guardados exitosamente. Redirigiendo...');
        // Redirigir después de un breve delay
        setTimeout(() => {
          window.location.href = document.referrer || '/';
        }, 1500);
      } else {
        this.mostrarError('❌ Error al guardar:\n\n' + resultado.errores.join('\n'));
      }
    } catch (error) {
      this.mostrarError('Error de red: ' + error.message);
    } finally {
      btnGuardar.textContent = textoOriginal;
      btnGuardar.disabled = false;
    }
  }

  /**
   * Muestra un mensaje de error al usuario.
   */
  mostrarError(mensaje) {
    alert(mensaje);
  }

  /**
   * Muestra un mensaje de éxito al usuario.
   */
  mostrarExito(mensaje) {
    alert(mensaje);
  }
}

// Inicializar al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
  const planIdMatch = window.location.pathname.match(/\/plan\/([^/]+)\/edit/);
  if (planIdMatch) {
    const planId = planIdMatch[1];
    new EditPlanForm('#form-edit-plan', planId);
  }
});
