// Utility functions
window.createTimeoutController = function(timeoutMs) {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), timeoutMs);
    return controller;
}

window.sleep = function(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Event Handlers
window.handleFolderChange = function(event) {
    window.location.href = `?selected_folder=${encodeURIComponent(event.target.value)}`;
}

window.sortTable = function(columnIndex) {
    const table = document.querySelector('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Get current sort direction
    const currentDirection = tbody.getAttribute('data-sort-direction') === 'asc' ? 1 : -1;
    const currentColumn = parseInt(tbody.getAttribute('data-sort-column'));
    
    // Determine new sort direction
    const newDirection = (columnIndex === currentColumn) ? -currentDirection : 1;
    
    // Sort the rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        if (aValue === bValue) return 0;
        return aValue > bValue ? newDirection : -newDirection;
    });
    
    // Update the table
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort indicators
    tbody.setAttribute('data-sort-direction', newDirection === 1 ? 'asc' : 'desc');
    tbody.setAttribute('data-sort-column', columnIndex);
    
    // Save sort state
    saveTableState();
}

// Save table sort state
window.saveTableState = function() {
    const tbody = document.querySelector('tbody');
    const state = {
        column: tbody.getAttribute('data-sort-column'),
        direction: tbody.getAttribute('data-sort-direction')
    };
    localStorage.setItem('tableSortState', JSON.stringify(state));
}

// Restore table sort state
window.restoreTableState = function() {
    const savedState = localStorage.getItem('tableSortState');
    if (savedState) {
        const state = JSON.parse(savedState);
        const tbody = document.querySelector('tbody');
        tbody.setAttribute('data-sort-column', state.column);
        tbody.setAttribute('data-sort-direction', state.direction);
        sortTable(parseInt(state.column));
    }
}

window.moveMovie = async function(moviePath, baseFolder, genre) {
    const escapedPath = typeof CSS !== 'undefined' ? CSS.escape(moviePath) : moviePath;
    const button = document.querySelector(`.move-button[data-path="${escapedPath}"]`);
    if (!button) return;

    const buttonText = button.querySelector('.button-text');
    const spinner = button.querySelector('.spinner-border');
    const retryText = button.querySelector('.retry-text');

    // Show loading state
    buttonText.classList.add('d-none');
    spinner.classList.remove('d-none');
    retryText.classList.add('d-none');

    try {
        const response = await fetch('/move_movie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: moviePath,
                base_folder: baseFolder,
                genre: genre
            })
        });

        if (!response.ok) {
            throw new Error('Failed to move movie');
        }

        // Remove the row after successful move
        const row = button.closest('tr');
        if (row) {
            row.remove();
        }

    } catch (error) {
        console.error('Error moving movie:', error);
        
        // Show retry state
        buttonText.classList.add('d-none');
        spinner.classList.add('d-none');
        retryText.classList.remove('d-none');
        
        if (typeof alert === 'function') {
            alert('Failed to move movie. Please try again.');
        }
    }
}

window.createMoveButton = function(moviePath, baseFolder, genre) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn-success btn-sm move-button';
    button.innerHTML = `
        <span class="button-text">Move to ${genre}</span>
        <div class="spinner-border spinner-border-sm d-none" role="status">
            <span class="visually-hidden">Moving...</span>
        </div>
        <span class="retry-text d-none">Try again</span>
    `;
    
    button.dataset.path = moviePath;
    button.dataset.baseFolder = baseFolder;
    button.dataset.genre = genre;
    
    button.addEventListener('click', function() {
        moveMovie(this.dataset.path, this.dataset.baseFolder, this.dataset.genre);
    });
    
    return button;
}

window.handleGenreSelection = async function(event, moviePath, baseFolder, genre, action) {
    try {
        let selectedGenre = genre;

        if (action === 'custom') {
            const newGenre = prompt('Enter new genre name:');
            if (!newGenre) return;
            selectedGenre = newGenre.trim();
        }

        if (action === 'add' || action === 'custom') {
            const response = await fetch('/add_genre', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    genre: selectedGenre
                })
            });

            if (!response.ok) {
                throw new Error('Failed to add genre');
            }
        }

        // Find the row from the clicked dropdown item
        const row = event.target.closest('tr');
        if (!row) {
            throw new Error('Could not find movie row');
        }

        // Update suggested genre text
        const suggestionCell = row.querySelector('.suggestion-cell');
        if (!suggestionCell) {
            throw new Error('Could not find suggestion cell');
        }
        
        const genreText = suggestionCell.querySelector('span');
        if (genreText) {
            genreText.textContent = selectedGenre;
        }

        // Update actions cell if genre is different from current
        const currentGenreCell = row.querySelector('.current-genre');
        if (!currentGenreCell) {
            throw new Error('Could not find current genre cell');
        }
        
        const currentGenre = currentGenreCell.textContent.trim();

        if (currentGenre.toLowerCase() !== selectedGenre.toLowerCase()) {
            const actionCell = row.querySelector('.actions-cell');
            if (!actionCell) {
                throw new Error('Could not find action cell');
            }

            // Clear the action cell and append the new move button
            actionCell.innerHTML = '';
            const moveButton = createMoveButton(moviePath, baseFolder, selectedGenre);
            actionCell.appendChild(moveButton);
        }

    } catch (error) {
        console.error('Error handling genre selection:', error);
        if (typeof alert === 'function') {
            alert('Failed to update genre. Please try again.');
        }
    }
}

window.getGenreSuggestion = async function(button) {
    const cell = button.closest('.suggestion-cell');
    if (!cell) {
        console.error('Could not find suggestion cell');
        return;
    }

    const container = cell.querySelector('.suggestion-container');
    if (!container) {
        console.error('Could not find container');
        return;
    }

    const row = cell.closest('tr');
    if (!row) {
        console.error('Could not find movie row');
        return;
    }

    const path = button.dataset.path;
    const baseFolder = button.dataset.baseFolder;
    if (!path || !baseFolder) {
        console.error('Missing path or base folder data');
        return;
    }

    // Show loading state
    const originalContent = container.innerHTML;
    container.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span>Getting suggestion...</span>
        </div>`;
    
    try {
        const response = await fetch('/suggest_genre', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: path,
                base_folder: baseFolder
            })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }

        // Update genre text and create dropdown
        container.innerHTML = `
            <span class="me-2 text-truncate">${data.genre}</span>
            <div class="dropdown">
                <button type="button" class="btn btn-link btn-sm p-0 edit-suggestion-button" data-bs-toggle="dropdown">
                    <i class="bi bi-pencil-square"></i>
                </button>
                <ul class="dropdown-menu p-2" style="min-width: 200px;" data-bs-popper="static">
                    <li>
                        <button class="dropdown-item" onclick="handleGenreSelection(event, '${path}', '${baseFolder}', '${data.genre}', 'add')">
                            Add "${data.genre}" as new genre
                        </button>
                    </li>
                    <li>
                        <button class="dropdown-item" onclick="handleGenreSelection(event, '${path}', '${baseFolder}', '', 'custom')">
                            Add custom genre...
                        </button>
                    </li>
                    <li><hr class="dropdown-divider"></li>
                    <li><h6 class="dropdown-header">Existing Genres</h6></li>
                    ${configuredGenres.map(genre => `
                        <li>
                            <button class="dropdown-item" onclick="handleGenreSelection(event, '${path}', '${baseFolder}', '${genre}', 'select')">
                                ${genre}
                            </button>
                        </li>
                    `).join('')}
                </ul>
            </div>`;

        // Get the current genre and update action cell if different
        const currentGenreCell = row.querySelector('.current-genre');
        if (!currentGenreCell) {
            throw new Error('Could not find current genre cell');
        }
        
        const currentGenre = currentGenreCell.textContent.trim();
        if (currentGenre.toLowerCase() !== data.genre.toLowerCase()) {
            const actionCell = row.querySelector('.actions-cell');
            if (!actionCell) {
                throw new Error('Could not find action cell');
            }

            // Clear the action cell and append the new move button
            actionCell.innerHTML = '';
            const moveButton = createMoveButton(path, baseFolder, data.genre);
            actionCell.appendChild(moveButton);
        }
        
    } catch (error) {
        console.error('Error getting suggestion:', error);
        container.innerHTML = `
            <div class="text-danger">
                <i class="bi bi-exclamation-circle me-1"></i>
                Error getting suggestion. Please try again.
            </div>`;
        
        // Restore original content after 3 seconds
        setTimeout(() => {
            container.innerHTML = originalContent;
        }, 3000);
    }
}

window.applyAllActions = async function() {
    const moveButtons = document.querySelectorAll('.move-button');
    const total = moveButtons.length;
    let completed = 0;
    let failed = 0;

    // Create progress alert
    const progressAlert = document.createElement('div');
    progressAlert.className = 'alert alert-info position-fixed bottom-0 end-0 m-3';
    progressAlert.style.minWidth = '300px';
    progressAlert.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <strong>Moving movies...</strong>
            <span>${completed}/${total}</span>
        </div>
        <div class="progress">
            <div class="progress-bar" role="progressbar" style="width: 0%"></div>
        </div>`;
    document.body.appendChild(progressAlert);

    // Process each move button
    for (const button of moveButtons) {
        const { path, baseFolder, genre } = button.dataset;
        try {
            await moveMovie(path, baseFolder, genre);
            completed++;
        } catch (error) {
            console.error('Failed to move movie:', error);
            failed++;
        }

        // Update progress
        const progress = ((completed + failed) / total) * 100;
        const progressBar = progressAlert.querySelector('.progress-bar');
        progressBar.style.width = `${progress}%`;
        const progressText = progressAlert.querySelector('span');
        progressText.textContent = `${completed}/${total}`;
    }

    // Show completion alert
    progressAlert.className = 'alert alert-success position-fixed bottom-0 end-0 m-3';
    progressAlert.innerHTML = `
        <strong>Complete!</strong> Successfully moved ${completed} movies.
        ${failed > 0 ? `<br>Failed to move ${failed} movies.` : ''}`;

    // Remove alert after 5 seconds
    setTimeout(() => {
        progressAlert.remove();
    }, 5000);
}

window.initializeTooltips = function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'click',
            html: true
        });
    });

    // Hide tooltip when clicking anywhere else
    document.addEventListener('click', function (event) {
        if (!event.target.closest('[data-bs-toggle="tooltip"]')) {
            tooltipTriggerList.forEach(function (tooltipTriggerEl) {
                const tooltip = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
                if (tooltip) {
                    tooltip.hide();
                }
            });
        }
    });

    // Hide other tooltips when showing a new one
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        tooltipTriggerEl.addEventListener('show.bs.tooltip', function () {
            tooltipTriggerList.forEach(function (otherTriggerEl) {
                if (otherTriggerEl !== tooltipTriggerEl) {
                    const tooltip = bootstrap.Tooltip.getInstance(otherTriggerEl);
                    if (tooltip) {
                        tooltip.hide();
                    }
                }
            });
        });
    });
}

window.attachEventListeners = function() {
    // Attach suggestion button listeners
    document.querySelectorAll('.suggestion-button').forEach(button => {
        button.addEventListener('click', function() {
            getGenreSuggestion(this);
        });
    });

    // Attach move button listeners
    document.querySelectorAll('.move-button').forEach(button => {
        button.addEventListener('click', function() {
            const { path, baseFolder, genre } = this.dataset;
            moveMovie(path, baseFolder, genre);
        });
    });
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createTimeoutController,
        sleep,
        handleFolderChange,
        sortTable,
        saveTableState,
        restoreTableState,
        moveMovie,
        createMoveButton,
        handleGenreSelection,
        getGenreSuggestion,
        applyAllActions
    };
}
