document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all tabs and contents
            tabButtons.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            const activeContent = document.getElementById(tabId);
            if (activeContent) {
                activeContent.classList.add('active');
            }
        });
    });
    
    // Initialize: show first tab by default
    if (tabButtons.length > 0) {
        tabButtons[0].classList.add('active');
        const firstContentId = tabButtons[0].getAttribute('data-tab');
        const firstContent = document.getElementById(firstContentId);
        if (firstContent) {
            firstContent.classList.add('active');
        }
    }
    
    // Initialize KPI values with placeholder data
    document.getElementById('kpi-total').textContent = '0';
    document.getElementById('kpi-pagado').textContent = '0';
    document.getElementById('kpi-pendiente').textContent = '0';
    
    // Sample data for demonstration
    const sampleData = {
        total: 15000,
        pagado: 8500,
        pendiente: 6500
    };
    
    // Update KPIs after a short delay to show the animation
    setTimeout(() => {
        document.getElementById('kpi-total').textContent = sampleData.total;
        document.getElementById('kpi-pagado').textContent = sampleData.pagado;
        document.getElementById('kpi-pendiente').textContent = sampleData.pendiente;
    }, 500);
    
    // Form submission handler
    const settingsForm = document.querySelector('.settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(settingsForm);
            // Here you would send the form data or update the dashboard settings
            alert('Configuración guardada para el dashboard Bera');
        });
    }
    
    // Sample data initialization
    console.log('Dashboard Bera inicializado');
    console.log('Datos muestrales:', {
        total: document.getElementById('kpi-total').textContent,
        pagado: document.getElementById('kpi-pagado').textContent,
        pendiente: document.getElementById('kpi-pendiente').textContent
    });
</script>