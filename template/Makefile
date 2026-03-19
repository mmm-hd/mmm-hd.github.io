# 1. Find the standard root pages (src_projects.m4 -> projects.html)
# We filter OUT the team pages here so they don't get built in the root folder!
ROOT_SRCS = $(filter-out src_team_%.m4, $(wildcard src_*.m4))
ROOT_TARGETS = $(ROOT_SRCS:src_%.m4=%.html)

# 2. Find the team pages (src_team_petra.m4 -> team/petra/index.html)
TEAM_SRCS = $(wildcard src_team_*.m4)
TEAM_TARGETS = $(patsubst src_team_%.m4, team/%/index.html, $(TEAM_SRCS))

# 3. The default command builds both the root pages and the subpages
all: $(ROOT_TARGETS) $(TEAM_TARGETS)

# 4. Rule to build standard root pages
%.html: src_%.m4 header.m4
	@echo "Building $@..."
	m4 $< > $@

# 5. Rule to build team subpages!
team/%/index.html: src_team_%.m4 header.m4
	@echo "Building $@..."
	@mkdir -p $(@D)
	m4 $< > $@

# 6. Clean command completely wipes generated HTML and the team folder
clean:
	@echo "Cleaning up HTML files..."
	rm -f $(ROOT_TARGETS)
	rm -rf team/

.PHONY: all clean
