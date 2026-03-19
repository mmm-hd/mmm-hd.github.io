from livereload import Server, shell

server = Server()

# 1. If any .m4 file changes, run 'make' automatically
server.watch('*.m4', shell('make'))

# 2. If the Makefile changes, run 'make'
server.watch('Makefile', shell('make'))

# 3. Watch the CSS and JS files for changes (no make needed, just reload)
server.watch('*.css')
server.watch('*.js')

print("Starting development server...")
print("Watching for changes. Press Ctrl+C to stop.")

# Serve the current directory
server.serve(root='.', port=8000)
