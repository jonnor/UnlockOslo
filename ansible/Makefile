MITOGEN_V=0.2.5

all: mitogen

mitogen: ../mitogen-$(MITOGEN_V)
../mitogen-$(MITOGEN_V):
	cd .. && \
	  wget https://files.pythonhosted.org/packages/source/m/mitogen/mitogen-$(MITOGEN_V).tar.gz && \
	  tar xf mitogen-$(MITOGEN_V).tar.gz && \
	  rm mitogen-$(MITOGEN_V).tar.gz
