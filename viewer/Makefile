.PHONY: upload

all: upload

upload:
	aws --profile=repo s3 sync --acl public-read --exclude=Makefile ./ s3://cadams-inside-baseball/
