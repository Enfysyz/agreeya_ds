# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files first to cache dependencies
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend code
COPY . .

# Expose the standard Vite port
EXPOSE 5173

# Run the dev server
CMD ["npm", "run", "dev"]