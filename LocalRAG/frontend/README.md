# Legal-RAG Frontend

This is the **frontend** of the **Legal-RAG** project, which serves as a user interface for interacting with document uploads, query submissions, and AI-generated responses. The frontend is built using **React** and communicates with the backend via APIs to perform file uploads and handle user queries.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Contributing](#contributing)
- [License](#license)

## Features

- **File Uploads**: Allows users to upload PDF documents to be processed for querying.
- **Query Interface**: Users can submit questions related to the uploaded documents, and the system returns AI-generated answers.
- **Real-time Feedback**: Loading indicators and status messages are provided for a better user experience.

## Installation

### Prerequisites

Make sure you have the following installed on your machine:
- **Node.js** (v14 or higher)
- **npm** (Node Package Manager)

### Step 1: Clone the repository
First, clone the repository from GitHub (replace the URL with your actual repository):

```bash
git clone https://github.com/yourusername/Legal-rag-frontend.git
cd Legal-rag-frontend
```

### Step 2: Install dependencies
Run the following command to install the necessary dependencies:

```bash
npm install
```

### Step 3: Configuration
- If you need to configure API endpoints or environment variables, you can do so in an `.env` file.
- Example of `.env`:

```bash
REACT_APP_BACKEND_URL=http://localhost:8000
```

### Step 4: Run the project

To start the development server, run:

```bash
npm start
```

This will launch the React development server and you can view the application in your browser at:

```
http://localhost:3000
```

## Usage

1. **Upload a PDF**: Use the "Upload New File" button to upload a PDF document. Once uploaded, the backend will process the document and generate embeddings.
2. **Ask a Question**: After uploading a PDF, you can type a query in the input box and press "Send". The AI will return an answer based on the contents of the uploaded document.
3. **View Responses**: Both your question and the AI’s answer will be displayed in the chatbox interface.

## Project Structure

```plaintext
src/
│
├── components/          # Contains React components (e.g., FileUpload, ChatBox, etc.)
├── styles/              # CSS files for styling components
├── App.js               # Main React component rendering the app
├── index.js             # Entry point for the app
└── assets/              # Static assets like images, icons, etc.
```

## Technologies

The frontend is built with:

- **React**: JavaScript library for building user interfaces.
- **Axios**: Used for making HTTP requests to the backend.
- **React-Top-Loading-Bar**: Displays a loading bar during file uploads and queries.
- **CSS**: Styling the UI elements.

## Contributing

We welcome contributions to improve the project! Here’s how you can help:

1. Fork the repository.
2. Create a new feature branch: `git checkout -b feature-branch-name`.
3. Commit your changes: `git commit -m 'Add new feature'`.
4. Push the branch: `git push origin feature-branch-name`.
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.


Copy and paste this markdown text into your README file, and it will format correctly when viewed on GitHub or any markdown viewer.





# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
