import os,re,html
POSTS=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','site','content','posts')
def add_faq(slug, qa):
    """Append a Frequently asked questions block to the END of a post. Never touches the intro or any existing text."""
    p=os.path.join(POSTS,slug+'.md'); t=open(p).read()
    assert 'class="faq"' not in t, slug
    blk='\n\n<div class="faq"><h2>Frequently asked questions</h2>\n'
    for q,a in qa: blk+=f'\n<h3>{q}</h3>\n<p>{a}</p>\n'
    blk+='\n</div>\n'
    open(p,'w').write(t.rstrip('\n')+blk)
