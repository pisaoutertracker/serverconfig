FROM library/almalinux
RUN yum install -y wget git llvm-toolset  cmake3  boost-devel  
RUN yum install -y epel-release 
RUN yum install -y pugixml-devel
#USER cms
RUN mkdir -p workdir
WORKDIR ./workdir  
RUN git  clone --recurse-submodules https://gitlab.cern.ch/cms_tk_ph2/power_supply.git  
RUN cd  power_supply/NetworkUtils   &&   git checkout AR_tests
#RUN cd power_supply/ &&  git checkout fixOVVcaen 
RUN cd power_supply/    # &&  git checkout master 
RUN ls /
COPY CAENHVWrapper-6.3.tgz /CAENHVWrapper-6.3.tgz
RUN tar -xzvf /CAENHVWrapper-6.3.tgz && cd CAENHVWrapper-6.3 && ./install.sh
RUN cd power_supply && mkdir build  && cd build && cmake .. && make -j 8
#RUN timedatectl set-timezone Europe/Rome
EXPOSE 7000
#CMD ["power_supply/bin/PowerSupplyController","-c", "/config.xml"]
CMD ["/bin/bash","/caen_server.sh"]
