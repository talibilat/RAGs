FROM node:20-slim AS base

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Set environment variables
ENV NEXT_PUBLIC_API_BASE=http://localhost:8000

# Build the application
RUN npm run build

# Expose the port
EXPOSE 3000

# Command to run the development server
CMD ["npm", "run", "dev"]
