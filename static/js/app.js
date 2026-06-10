document.addEventListener('DOMContentLoaded', () => {
    // --- Dark/Light Mode Management ---
    const themeToggleBtns = document.querySelectorAll('.theme-toggle-btn');
    
    // Read stored theme or default to system
    let currentTheme = localStorage.getItem('theme');
    if (!currentTheme) {
        currentTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    // Apply theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcons(currentTheme);
    
    themeToggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const target = current === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', target);
            localStorage.setItem('theme', target);
            updateThemeIcons(target);
            showToast("Theme Updated", `Switched to ${target} mode.`);
        });
    });
    
    function updateThemeIcons(theme) {
        themeToggleBtns.forEach(btn => {
            const icon = btn.querySelector('i');
            if (!icon) return;
            if (theme === 'dark') {
                icon.className = 'fas fa-sun';
            } else {
                icon.className = 'fas fa-moon';
            }
        });
    }

    // --- Mobile Sidebar Toggle ---
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.app-sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebarToggle && sidebar && overlay) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        });
        
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    // --- Toast Notifications ---
    window.showToast = function(title, message, type = 'primary') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast-premium mb-3 animate__animated animate__fadeInUp`;
        
        // border color based on type
        let borderClass = 'border-primary';
        if (type === 'success') borderClass = 'border-success';
        if (type === 'danger') borderClass = 'border-danger';
        
        toast.innerHTML = `
            <div class="toast-premium-header border-bottom ${borderClass}">
                <strong class="text-${type}"><i class="fas fa-info-circle me-1"></i> ${title}</strong>
                <button type="button" class="btn-close" style="font-size: 0.75rem; filter: var(--text-primary) == '#f8fafc' ? 'invert(1)' : 'none';" onclick="this.closest('.toast-premium').remove()"></button>
            </div>
            <div class="toast-premium-body">
                ${message}
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 3.5 seconds
        setTimeout(() => {
            toast.classList.replace('animate__fadeInUp', 'animate__fadeOutDown');
            setTimeout(() => toast.remove(), 500);
        }, 3500);
    };

    // --- Copy Quote to Clipboard ---
    document.addEventListener('click', async (e) => {
        const copyBtn = e.target.closest('.copy-btn');
        if (!copyBtn) return;
        
        const text = copyBtn.getAttribute('data-quote-text');
        const author = copyBtn.getAttribute('data-quote-author');
        const formatted = `"${text}" — ${author}`;
        
        try {
            await navigator.clipboard.writeText(formatted);
            
            // Success animation/state on button
            copyBtn.classList.add('copied-active');
            const icon = copyBtn.querySelector('i');
            const origClass = icon.className;
            icon.className = 'fas fa-check';
            
            showToast("Copied to Clipboard", "Quote text copied successfully!", "success");
            
            setTimeout(() => {
                copyBtn.classList.remove('copied-active');
                icon.className = origClass;
            }, 2000);
        } catch (err) {
            showToast("Copy Failed", "Could not copy quote text.", "danger");
        }
    });

    // --- Favorite Toggle (AJAX) ---
    document.addEventListener('click', async (e) => {
        const favBtn = e.target.closest('.favorite-btn');
        if (!favBtn) return;
        
        const quoteId = favBtn.getAttribute('data-quote-id');
        
        try {
            const response = await fetch(`/api/favorite/${quoteId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                const icon = favBtn.querySelector('i');
                const textSpan = favBtn.querySelector('.fav-btn-text');
                
                if (data.action === 'added') {
                    icon.className = 'fas fa-heart text-danger';
                    favBtn.classList.add('active');
                    if (textSpan) textSpan.textContent = 'Favorited';
                    showToast("Added to Favorites", "Saved to your favorites catalog.", "success");
                } else {
                    icon.className = 'far fa-heart';
                    favBtn.classList.remove('active');
                    if (textSpan) textSpan.textContent = 'Favorite';
                    showToast("Removed from Favorites", "Quote removed from favorites.", "primary");
                    
                    // If we are on the favorites page, remove the card dynamically
                    if (window.location.pathname === '/favorites') {
                        const card = favBtn.closest('.col-12, .col-md-6, .col-lg-4, .card-premium');
                        if (card) {
                            card.classList.add('animate__animated', 'animate__fadeOut');
                            setTimeout(() => card.remove(), 500);
                        }
                    }
                }
            } else {
                showToast("Error", data.message || "Failed to toggle favorite status.", "danger");
            }
        } catch (err) {
            showToast("Network Error", "Could not reach server.", "danger");
        }
    });

    // --- AJAX Random Quote Generation ---
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            const icon = generateBtn.querySelector('i');
            const textSpan = generateBtn.querySelector('span');
            
            // Loading state
            icon.classList.add('spin-anim');
            generateBtn.disabled = true;
            if (textSpan) textSpan.textContent = 'Generating...';
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    const quote = data.quote;
                    
                    // Fade out existing elements, update and fade in
                    const container = document.getElementById('random-quote-container');
                    container.classList.add('animate__animated', 'animate__fadeOut');
                    
                    setTimeout(() => {
                        // Update text
                        document.getElementById('random-quote-text').textContent = quote.text;
                        document.getElementById('random-quote-author').textContent = quote.author;
                        
                        // Update buttons attributes
                        const favBtn = document.getElementById('random-fav-btn');
                        const copyBtn = document.getElementById('random-copy-btn');
                        const exportBtn = document.getElementById('random-export-btn');
                        
                        favBtn.setAttribute('data-quote-id', quote.id);
                        copyBtn.setAttribute('data-quote-text', quote.text);
                        copyBtn.setAttribute('data-quote-author', quote.author);
                        exportBtn.setAttribute('data-quote-text', quote.text);
                        exportBtn.setAttribute('data-quote-author', quote.author);
                        
                        // Update favorite button icon state
                        const favIcon = favBtn.querySelector('i');
                        if (quote.is_favorite) {
                            favIcon.className = 'fas fa-heart text-danger';
                            favBtn.classList.add('active');
                        } else {
                            favIcon.className = 'far fa-heart';
                            favBtn.classList.remove('active');
                        }
                        
                        // Update dropdown menu items for quick collection addition
                        const dropdownItems = document.querySelectorAll('.add-to-coll-item');
                        dropdownItems.forEach(item => {
                            item.setAttribute('data-quote-id', quote.id);
                        });
                        
                        // Remove animation classes and fade in
                        container.classList.remove('animate__fadeOut');
                        container.classList.add('animate__fadeIn');
                        setTimeout(() => container.classList.remove('animate__fadeIn'), 500);
                        
                    }, 400);
                    
                } else {
                    showToast("Generation Failed", data.message || "Could not fetch a new quote.", "danger");
                }
            } catch (err) {
                showToast("Network Error", "Unable to connect to the quote provider.", "danger");
            } finally {
                icon.classList.remove('spin-anim');
                generateBtn.disabled = false;
                if (textSpan) textSpan.textContent = 'Generate Random Quote';
            }
        });
    }

    // --- HTML5 Canvas Quote Card Export (html2canvas) ---
    document.addEventListener('click', (e) => {
        const exportBtn = e.target.closest('.export-btn');
        if (!exportBtn) return;
        
        const text = exportBtn.getAttribute('data-quote-text');
        const author = exportBtn.getAttribute('data-quote-author');
        
        // Populate the hidden export card template
        const exportTarget = document.getElementById('export-render-canvas');
        if (!exportTarget) return;
        
        exportTarget.querySelector('.export-quote-text').textContent = text;
        exportTarget.querySelector('.export-quote-author').textContent = author;
        
        // Show loading toast since rendering takes a split second
        showToast("Generating Image", "Rendering your premium quote card snapshot...", "primary");
        
        // Force font rendering & run html2canvas
        html2canvas(exportTarget, {
            scale: 2, // High resolution
            useCORS: true,
            backgroundColor: null,
            logging: false
        }).then(canvas => {
            const dataUrl = canvas.toDataURL('image/png');
            
            // Create download anchor
            const link = document.createElement('a');
            const sanitizedAuthor = author.replace(/[^a-z0-9]/gi, '_').toLowerCase();
            link.download = `quotehub_${sanitizedAuthor}.png`;
            link.href = dataUrl;
            link.click();
            
            showToast("Export Successful", "PNG image downloaded successfully!", "success");
        }).catch(err => {
            showToast("Export Failed", "Error rendering canvas: " + err.message, "danger");
        });
    });

    // --- Custom Collections Creation ---
    const createCollectionForm = document.getElementById('create-collection-form');
    if (createCollectionForm) {
        createCollectionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const nameInput = document.getElementById('collection-name');
            const descInput = document.getElementById('collection-desc');
            const name = nameInput.value.strip ? nameInput.value.strip() : nameInput.value.trim();
            const desc = descInput.value.strip ? descInput.value.strip() : descInput.value.trim();
            
            try {
                const response = await fetch('/api/collections', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name, description: desc })
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    showToast("Collection Created", `"${name}" collection added.`, "success");
                    nameInput.value = '';
                    descInput.value = '';
                    
                    // Close Bootstrap Modal if open
                    const modalEl = document.getElementById('createCollectionModal');
                    if (modalEl) {
                        const modalInstance = bootstrap.Modal.getInstance(modalEl);
                        if (modalInstance) modalInstance.hide();
                    }
                    
                    // Reload page to reflect collection changes
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    showToast("Creation Failed", data.message || "Failed to create collection.", "danger");
                }
            } catch (err) {
                showToast("Network Error", "Unable to create collection.", "danger");
            }
        });
    }

    // --- Add Quote to Custom Collection ---
    document.addEventListener('click', async (e) => {
        const item = e.target.closest('.add-to-coll-item');
        if (!item) return;
        
        e.preventDefault();
        const collectionId = item.getAttribute('data-collection-id');
        const quoteId = item.getAttribute('data-quote-id');
        const collectionName = item.textContent.trim();
        
        try {
            const response = await fetch(`/api/collections/${collectionId}/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quote_id: quoteId })
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                showToast("Added to Collection", `Saved to "${collectionName}".`, "success");
            } else {
                showToast("Already Present", data.message || "Quote is already in this collection.", "warning");
            }
        } catch (err) {
            showToast("Network Error", "Could not associate quote with collection.", "danger");
        }
    });

    // --- Remove Quote from Collection (AJAX) ---
    document.addEventListener('click', async (e) => {
        const removeBtn = e.target.closest('.remove-from-coll-btn');
        if (!removeBtn) return;
        
        const collectionId = removeBtn.getAttribute('data-collection-id');
        const quoteId = removeBtn.getAttribute('data-quote-id');
        
        try {
            const response = await fetch(`/api/collections/${collectionId}/remove/${quoteId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                showToast("Removed", "Quote removed from collection.", "primary");
                
                // Remove row/card from UI
                const row = removeBtn.closest('.col-12, .col-md-6, .col-lg-4, tr');
                if (row) {
                    row.classList.add('animate__animated', 'animate__fadeOut');
                    setTimeout(() => row.remove(), 500);
                }
            } else {
                showToast("Error", data.message || "Failed to remove quote.", "danger");
            }
        } catch (err) {
            showToast("Network Error", "Could not contact server.", "danger");
        }
    });

    // --- Delete custom collection (AJAX) ---
    document.addEventListener('click', async (e) => {
        const deleteBtn = e.target.closest('.delete-collection-btn');
        if (!deleteBtn) return;
        
        if (!confirm("Are you sure you want to delete this collection? All saved mappings inside it will be removed permanently.")) {
            return;
        }
        
        const collectionId = deleteBtn.getAttribute('data-collection-id');
        
        try {
            const response = await fetch(`/api/collections/${collectionId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                showToast("Collection Deleted", "The collection was deleted successfully.", "success");
                
                // Remove card from UI
                const card = deleteBtn.closest('.col-12, .col-md-6, .col-lg-4');
                if (card) {
                    card.classList.add('animate__animated', 'animate__fadeOut');
                    setTimeout(() => card.remove(), 500);
                } else {
                    setTimeout(() => window.location.href = '/collections', 800);
                }
            } else {
                showToast("Error", data.message || "Failed to delete collection.", "danger");
            }
        } catch (err) {
            showToast("Network Error", "Failed to communicate deletion command.", "danger");
        }
    });
});
