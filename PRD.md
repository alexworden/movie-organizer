# Movie Organizer - Product Requirements Document

## Overview
Movie Organizer is a web-based application designed to help users organize their movie files by automatically categorizing them into genre-based folders. The application leverages AI technology to suggest appropriate genres for movies and provides an intuitive interface for managing movie files.

## Target Users

### Primary Users
- Movie collectors with large digital libraries
- Home media server administrators
- Media enthusiasts who maintain organized movie collections

### User Needs
1. **Organization**: Users need to maintain a well-organized movie collection
2. **Automation**: Users want to reduce manual effort in categorizing movies
3. **Accuracy**: Users need accurate genre suggestions for their movies
4. **Control**: Users want the ability to override automated suggestions
5. **Flexibility**: Users need to manage multiple movie folders and custom genres

## Product Features

### 1. Configuration Management
#### Requirements
- Users can configure multiple movie source folders
- Users can define and manage custom genres
- Configuration changes are persistent across sessions
- Interface provides clear feedback on configuration updates

### 2. Movie Management Interface
#### Requirements
- Display all movies from configured folders in a sortable table
- Show movie titles and current genres
- Support for large movie collections without performance degradation
- Maintain consistent layout during dynamic updates
- Exclude movies from any folders containing '#recycle' in their path
- Display full file path via info icon for each movie

### 3. Genre Suggestion System
#### Requirements
- Integration with OpenAI GPT-4 for intelligent genre suggestions
- Optional TMDB integration for additional genre data
- Support for custom API keys
- Error handling for API failures
- Rate limiting and cost optimization

### 4. Genre Assignment
#### Requirements
- One-click genre suggestion requests
- Ability to edit suggested genres
- Support for custom genre assignments
- Automatic file movement upon genre selection
- Undo/retry capability for failed operations

### 5. File Management
#### Requirements
- Automatic creation of genre folders
- Safe file movement operations
- Handling of file naming conflicts
- Preservation of original file names
- Error handling for file system operations
- Support for #recycle folders to exclude movies from display

## Technical Requirements

### Performance
- Page load time < 2 seconds
- Genre suggestion response < 5 seconds
- File movement operation < 3 seconds
- Support for libraries with 1000+ movies

### Security
- Secure storage of API keys
- Input validation for all user inputs
- Protection against path traversal attacks
- Secure handling of file operations

### Compatibility
- Support for major web browsers (Chrome, Firefox, Safari)
- Support for various video file formats
- Cross-platform compatibility (Windows, macOS, Linux)

### Reliability
- Graceful handling of API failures
- Recovery from interrupted file operations
- Data persistence across server restarts
- Logging of all critical operations

## User Interface

### Navigation
- Clear navigation between configuration and movies pages
- Consistent header with application branding
- Responsive design for various screen sizes

### Movie List View
- Sortable columns for movie title and current genre
- Clear indicators for sortable columns
- Consistent button styling and placement
- Visual feedback for loading states

### Genre Management
- Dropdown for genre selection
- Support for adding new genres
- Clear success/error feedback
- Progress indicators for operations

## Usage Scenarios

### Scenario 1: Initial Setup
1. User accesses application for the first time
2. Configures movie folders and genres
3. Saves configuration
4. Navigates to movie list
5. Movies in #recycle folders are automatically excluded

### Scenario 2: Genre Categorization
1. User views uncategorized movies
2. Requests genre suggestions
3. Reviews and approves suggestions
4. Movies are automatically moved to genre folders

### Scenario 3: Custom Categorization
1. User disagrees with suggested genre
2. Selects edit option
3. Chooses different genre or adds new genre
4. Confirms change and file is moved

### Scenario 4: Bulk Organization
1. User has multiple uncategorized movies
2. Requests suggestions for all
3. Reviews suggestions
4. Approves or modifies as needed

## Future Considerations

### Potential Enhancements
1. Batch operations for multiple movies
2. Advanced search and filtering
3. Movie metadata enrichment
4. Alternative genre suggestion sources
5. Integration with media servers
6. Movie poster and description display
7. Support for TV shows and other media types

### Scalability Considerations
1. Caching for API responses
2. Pagination for large libraries
3. Background processing for file operations
4. Database integration for larger deployments

## Success Metrics
1. Time saved in movie organization
2. Accuracy of genre suggestions
3. User satisfaction with interface
4. System reliability and uptime
5. API cost optimization
