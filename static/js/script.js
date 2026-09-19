//Ejecutando funciones
document.getElementById("btn__iniciar-sesion").addEventListener("click", iniciarSesion);
document.getElementById("btn__registrarse").addEventListener("click", register);
window.addEventListener("resize", anchoPage);
document.getElementById("pais").addEventListener("change", function () {
    const paisSeleccionado = this.value;
    const ciudadSelect = document.getElementById("ciudad");

    // Limpiar las opciones de ciudad
    ciudadSelect.innerHTML = '<option value="" disabled selected>Selecciona tu ciudad</option>';

    // Hacer una solicitud al servidor para obtener las ciudades
    fetch(`/obtener_ciudades/${paisSeleccionado}`)
        .then(response => response.json())
        .then(ciudades => {
            ciudades.forEach(ciudad => {
                const option = document.createElement("option");
                option.value = ciudad;
                option.textContent = ciudad;
                ciudadSelect.appendChild(option);
            });
        })
        .catch(error => console.error("Error al obtener las ciudades:", error));
});

//Declarando variables
var formulario_login = document.querySelector(".formulario__login");
var formulario_register = document.querySelector(".formulario__register");
var contenedor_login_register = document.querySelector(".contenedor__login-register");
var caja_trasera_login = document.querySelector(".caja__trasera-login");
var caja_trasera_register = document.querySelector(".caja__trasera-register");

    //FUNCIONES

// JavaScript function to show an error alert
function showErrorAlert(message) {
    const alertContainer = document.querySelector('.alert-container');
    alertContainer.innerHTML = `
        <div class="alert alert-error">
            ${message}
        </div>
    `;
    
    // Optional: Automatically hide the alert after a few seconds
    setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 5000); // Hide after 5 seconds
}

function anchoPage(){

    if (window.innerWidth > 850){
        caja_trasera_register.style.display = "block";
        caja_trasera_login.style.display = "block";
    }else{
        caja_trasera_register.style.display = "block";
        caja_trasera_register.style.opacity = "1";
        caja_trasera_login.style.display = "none";
        formulario_login.style.display = "block";
        contenedor_login_register.style.left = "0px";
        formulario_register.style.display = "none";   
    }
}

anchoPage();


    function iniciarSesion(){
        if (window.innerWidth > 850){
            formulario_login.style.display = "block";
            contenedor_login_register.style.left = "10px";
            formulario_register.style.display = "none";
            caja_trasera_register.style.opacity = "1";
            caja_trasera_login.style.opacity = "0";
        }else{
            formulario_login.style.display = "block";
            contenedor_login_register.style.left = "0px";
            formulario_register.style.display = "none";
            caja_trasera_register.style.display = "block";
            caja_trasera_login.style.display = "none";
        }
    }

    function register(){
        if (window.innerWidth > 850){
            formulario_register.style.display = "block";
            contenedor_login_register.style.left = "410px";
            formulario_login.style.display = "none";
            caja_trasera_register.style.opacity = "0";
            caja_trasera_login.style.opacity = "1";
        }else{
            formulario_register.style.display = "block";
            contenedor_login_register.style.left = "0px";
            formulario_login.style.display = "none";
            caja_trasera_register.style.display = "none";
            caja_trasera_login.style.display = "block";
            caja_trasera_login.style.opacity = "1";
        }
    }

    function validarContraseña() {
        const contraseña = document.getElementById('contraseña').value;
        const errores = [];

        // Verificar que la contraseña tenga al menos 8 caracteres
        if (contraseña.length < 8) {
            errores.push('Debe tener al menos 8 caracteres.');
        }

        // Verificar que la contraseña tenga al menos una letra mayúscula
        if (!/[A-Z]/.test(contraseña)) {
            errores.push('Debe incluir al menos una letra mayúscula.');
        }

        // Verificar que la contraseña tenga al menos un símbolo
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(contraseña)) {
            errores.push('Debe incluir al menos un carácter especial.');
        }

        // Verificar que la contraseña tenga al menos un número
        if (!/\d/.test(contraseña)) {
            errores.push('Debe incluir al menos un número.');
        }

        // Mostrar los errores en tiempo real
        const erroresDiv = document.getElementById('password-errors');
        if (errores.length > 0) {
            erroresDiv.innerHTML = errores.map(error => `<p>${error}</p>`).join('');
            erroresDiv.style.color = 'red';
        } else {
            erroresDiv.innerHTML = '<p>La contraseña es válida.</p>';
            erroresDiv.style.color = 'green';
        }
    }

    // Función para mostrar/ocultar la contraseña
    function togglePassword(fieldId) {
        const field = document.getElementById(fieldId);
        const toggle = field.nextElementSibling; // El ícono de ojo
        if (field.type === 'password') {
            field.type = 'text';
            toggle.textContent = '🙈'; // Cambiar el ícono a "ocultar"
        } else {
            field.type = 'password';
            toggle.textContent = '👁️'; // Cambiar el ícono a "mostrar"
        }
    }