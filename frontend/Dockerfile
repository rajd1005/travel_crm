# Use the official lightweight Node.js 18 image
FROM node:18-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json and package-lock.json (if available)
COPY package.json ./

# Install the JavaScript dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Expose port 3000 to match the docker-compose.yml configuration
EXPOSE 3000

# Start the React development server
CMD ["npm", "start"]
