.PHONY: all
all: resume.pdf

resume.pdf: resume.tex resume.dat fix.py
	pdflatex resume.tex
	python fix.py
	python3 make-recursive.py

resume.iso: /home/klange/Projects/workspace/toaru-nih/image.iso
	cp $< $@

resume.dat: resume.iso
	tail -c +27 resume.iso > resume.dat.1
	head -c 2048 resume.dat.1 > resume.dat.a
	tail -c +2049 resume.dat.1 > resume.dat.b
	tail -c +150 resume.dat.b > resume.dat.c
	-rm garbage -f
	dd if=/dev/zero of=garbage bs=781 count=1
	cat resume.dat.a resume.dat.c garbage > resume.dat
	rm resume.dat.a resume.dat.b resume.dat.c resume.dat.1

index.htm: template.htm resume.pdf build_index.py
	python3.6 build_index.py

.PHONY: go
go: resume.pdf index.htm
	scp resume.pdf dakko.us:public_html/resume/resume_iso.pdf
	scp index.htm dakko.us:public_html/resume/index.htm

.PHONY: clean
clean:
	-rm resume.{pdf,log}
