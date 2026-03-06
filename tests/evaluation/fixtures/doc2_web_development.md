# Web Development Fundamentals

## HTTP Protocol

HTTP (Hypertext Transfer Protocol) is the foundation of data communication on the World Wide Web. HTTP defines several request methods: GET retrieves data from a server, POST submits data for processing, PUT replaces an existing resource entirely, PATCH partially modifies a resource, and DELETE removes a specified resource. HTTP status codes indicate the outcome of a request: 200 means OK (successful), 201 means Created, 301 means Moved Permanently, 400 means Bad Request, 401 means Unauthorized, 403 means Forbidden, 404 means Not Found, and 500 means Internal Server Error. HTTP/2, published in 2015, introduced multiplexing, header compression, and server push to improve performance over HTTP/1.1.

## REST API Design

REST (Representational State Transfer) is an architectural style for designing networked applications. RESTful APIs organize data into resources, each identified by a unique URI (Uniform Resource Identifier). A well-designed REST API uses nouns for resource endpoints (e.g., /users, /products) rather than verbs. JSON (JavaScript Object Notation) is the most common data format for REST API request and response bodies. REST APIs should be stateless, meaning each request contains all information needed for the server to process it. The six constraints of REST are: client-server architecture, statelessness, cacheability, uniform interface, layered system, and code on demand (optional).

## FastAPI Framework

FastAPI is a modern Python web framework for building APIs, created by Sebastián Ramírez. FastAPI supports asynchronous request handling using Python's async and await keywords. It uses Python type hints for automatic request validation and serialization through Pydantic models. FastAPI automatically generates interactive API documentation using Swagger UI (available at /docs) and ReDoc (available at /redoc). FastAPI achieves performance comparable to Node.js and Go frameworks, making it one of the fastest Python web frameworks available. FastAPI uses dependency injection for managing shared resources like database connections and authentication.

## Authentication and Security

Web APIs commonly use token-based authentication. JSON Web Tokens (JWT) consist of three parts: a header, a payload, and a signature, separated by dots. OAuth 2.0 is the industry-standard protocol for authorization, supporting four grant types: authorization code, implicit, resource owner password credentials, and client credentials. CORS (Cross-Origin Resource Sharing) headers control which domains can access API resources. HTTPS encrypts data in transit using TLS (Transport Layer Security) to prevent man-in-the-middle attacks.

## Frontend Technologies

HTML (HyperText Markup Language) defines the structure and content of web pages using elements and tags. CSS (Cascading Style Sheets) controls the visual presentation, including layout, colors, and typography. JavaScript enables interactive behavior in web browsers through DOM (Document Object Model) manipulation. Modern frontend frameworks include React (maintained by Meta), Angular (maintained by Google), and Vue.js (created by Evan You). Single Page Applications (SPAs) load a single HTML page and dynamically update content using JavaScript, reducing server round-trips.

## API Versioning

API versioning prevents breaking changes for existing clients. Common versioning strategies include URL path versioning (e.g., /api/v1/users), query parameter versioning, custom header versioning, and content negotiation using Accept headers. Semantic versioning (SemVer) follows the MAJOR.MINOR.PATCH format where MAJOR indicates breaking changes, MINOR adds backward-compatible features, and PATCH includes backward-compatible bug fixes.
