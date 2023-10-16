FROM library/almalinux
RUN yum install -y vim wget git
RUN adduser cms
USER cms
WORKDIR /home/cms/work
RUN echo DIR `pwd` USER `whoami` LS `ls /opt`
RUN git clone --branch prod https://github.com/pisaoutertracker/testnode
RUN touch pippo

