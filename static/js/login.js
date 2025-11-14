let codigo = '';

function addDigit(digit) {
    if (codigo.length < 4) {
        codigo += digit;
        document.getElementById('codigo-input').value = '•'.repeat(codigo.length);
    }
}

function clearCodigo() {
    codigo = '';
    document.getElementById('codigo-input').value = '';
    document.getElementById('message').textContent = '';
    document.getElementById('message').className = 'message';
}

async function submitCodigo() {
    if (codigo.length !== 4) {
        showMessage('Ingrese un código de 4 dígitos', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ codigo })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('¡Bienvenido!', 'success');
            
            if (data.requires_caja) {
                setTimeout(() => {
                    document.getElementById('caja-modal').style.display = 'flex';
                }, 500);
            } else {
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);
            }
        } else {
            showMessage(data.message, 'error');
            clearCodigo();
        }
    } catch (error) {
        showMessage('Error de conexión', 'error');
        clearCodigo();
    }
}

async function submitCaja() {
    const monto = document.getElementById('monto-caja').value;
    
    // Validar que se haya ingresado un monto
    if (!monto || monto === '') {
        alert('Por favor ingrese un monto');
        return;
    }
    
    // Convertir a número y validar monto mínimo
    const montoNumero = parseFloat(monto);
    
    if (isNaN(montoNumero)) {
        alert('Por favor ingrese un monto válido');
        return;
    }
    
    if (montoNumero < 200) {
        alert('El monto mínimo de caja es de $200.00');
        document.getElementById('monto-caja').focus();
        return;
    }
    
    try {
        const response = await fetch('/api/set-caja', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ monto: montoNumero })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = '/cajero';
        } else {
            alert(data.message);
        }
    } catch (error) {
        alert('Error al configurar la caja');
        console.error(error);
    }
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
}
