FROM coinstac/coinstac-base-python-stream

# Set the working directory
WORKDIR /computation

# Copy the current directory contents into the container
# COPY requirements.txt /computation

#RUN apt-get update && apt-get install -y r-base

# Install any needed packages specified in requirements.txt
# RUN pip install -r requirements.txt

#apt-get install software-properties-common
#apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
#add-apt-repository ppa:marutter/rdev

RUN apt-get update \ 
	&& apt-get install -y --no-install-recommends \
		ed \
		less \
		locales \
		vim-tiny \
		wget \
		ca-certificates \
		fonts-texgyre \
	&& rm -rf /var/lib/apt/lists/*

## Configure default locale, see https://github.com/rocker-org/rocker/issues/19
#RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
#	&& locale-gen en_US.utf8 \
#	&& /usr/sbin/update-locale LANG=en_US.UTF-8

#ENV LC_ALL en_US.UTF-8
#ENV LANG en_US.UTF-8

## Use Debian unstable via pinning -- new style via APT::Default-Release
RUN echo "deb http://http.debian.net/debian sid main" > /etc/apt/sources.list.d/debian-unstable.list \
        && echo 'APT::Default-Release "testing";' > /etc/apt/apt.conf.d/default 

ENV R_BASE_VERSION 3.5.1

## Now install R and littler, and create a link for littler in /usr/local/bin
## Also set a default CRAN repo, and make sure littler knows about it too
## Also install stringr to make dococt install (from source) easier
RUN apt-get update \
	&& apt-get install -t unstable -y --no-install-recommends \
		r-base=${R_BASE_VERSION}-* \
		r-base-dev=${R_BASE_VERSION}-* \
		r-recommended=${R_BASE_VERSION}-* \
        && echo 'options(repos = c(CRAN = "https://cloud.r-project.org/"))' >> /etc/R/Rprofile.site \
    	&& rm -rf /tmp/downloaded_packages/ /tmp/*.rds \
    	&& rm -rf /var/lib/apt/lists/*

#CMD ["R"]
#RUN echo "r <- getOption('repos'); r['CRAN'] <- 'http://cran.us.r-project.org'; options(repos = r);" > ~/.Rprofile
RUN Rscript -e "install.packages('ppcor')"
RUN Rscript -e "install.packages('moments')"
RUN Rscript -e "install.packages('RCurl')"
RUN Rscript -e "install.packages('matrixStats')"

# Copy the current directory contents into the container
COPY . /computation