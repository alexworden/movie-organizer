/**
 * @jest-environment jsdom
 */

const {
    createMoveButton,
    handleGenreSelection,
    moveMovie
} = require('../../static/js/movies.js');

// Mock data
const mockMovies = [
    {
        title: "Test Movie 1",
        path: "/movies/test1.mp4",
        current_genre: "",
        suggested_genre: "Action"
    },
    {
        title: "Test Movie 2",
        path: "/movies/test2.mp4",
        current_genre: "Drama",
        suggested_genre: "Comedy"
    }
];

const mockConfig = {
    genres: ["Action", "Comedy", "Drama", "Horror"]
};

// Mock fetch responses
global.fetch = jest.fn((url) => {
    if (url === '/suggest_genre') {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ genre: 'Action' })
        });
    }
    if (url === '/add_genre') {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true })
        });
    }
    if (url === '/move_movie') {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true })
        });
    }
    return Promise.reject(new Error('Not found'));
});

describe('Movies Page Functionality', () => {
    beforeEach(() => {
        // Reset fetch mock
        fetch.mockClear();
        
        // Set up our document body
        document.body.innerHTML = `
            <table class="table table-hover">
                <tbody>
                    ${mockMovies.map((movie, index) => `
                        <tr>
                            <td class="movie-title">
                                <div class="d-flex align-items-center">
                                    <span class="me-2">${movie.title}</span>
                                    <button type="button" 
                                        class="btn btn-link btn-sm p-0 suggestion-button" 
                                        data-path="${movie.path}"
                                        data-base-folder="/movies">
                                        <i class="bi bi-lightbulb"></i>
                                    </button>
                                </div>
                            </td>
                            <td class="current-genre">${movie.current_genre}</td>
                            <td class="suggestion-cell">
                                <div class="suggestion-container">
                                    <button type="button" class="btn btn-link btn-sm p-0">
                                        Get Suggestion
                                    </button>
                                </div>
                            </td>
                            <td class="actions-cell" id="actions-${index + 1}"></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        // Mock the template variables
        window.configuredGenres = mockConfig.genres;
    });

    test('should create and append move button', () => {
        const actionCell = document.querySelector('.actions-cell');
        const button = createMoveButton('/test/path', '/base/folder', 'Action');
        actionCell.appendChild(button);

        expect(button.classList.contains('move-button')).toBe(true);
        expect(button.textContent).toContain('Move to Action');
    });

    test('should handle genre selection', async () => {
        // Create a mock event
        const row = document.querySelector('tr');
        const event = {
            target: document.createElement('button'),
            preventDefault: jest.fn()
        };
        event.target.closest = jest.fn().mockReturnValue(row);

        await handleGenreSelection(event, '/test/path', '/base/folder', 'Action', 'select');

        // Check if move button was created
        const moveButton = row.querySelector('.move-button');
        expect(moveButton).toBeTruthy();
        expect(moveButton.textContent).toContain('Move to Action');
    });

    test('should handle custom genre addition', async () => {
        // Mock the prompt function
        window.prompt = jest.fn(() => 'New Genre');

        // Create a mock event
        const row = document.querySelector('tr');
        const event = {
            target: document.createElement('button'),
            preventDefault: jest.fn()
        };
        event.target.closest = jest.fn().mockReturnValue(row);

        await handleGenreSelection(event, '/test/path', '/base/folder', '', 'custom');

        // Verify prompt was called
        expect(window.prompt).toHaveBeenCalled();
        expect(fetch).toHaveBeenCalledWith('/add_genre', expect.any(Object));
    });

    test('should handle movie move action', async () => {
        const actionCell = document.querySelector('.actions-cell');
        const button = createMoveButton('/test/path', '/base/folder', 'Action');
        actionCell.appendChild(button);

        await moveMovie('/test/path', '/base/folder', 'Action');

        // Verify move request was made
        expect(fetch).toHaveBeenCalledWith('/move_movie', expect.any(Object));
    });
});
