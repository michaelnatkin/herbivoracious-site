import glob,re
def info(prefix):
    fs=glob.glob(prefix+'*.md')
    if not fs: return None
    f=sorted(fs,key=len)[0]; s=open(f).read(); h=s.split('\n---\n',1)[0]
    d=re.search(r'^date:\s*(\d{4})-(\d\d)',h,re.M); sl=re.search(r'^slug:\s*"?([^"\n]+)"?',h,re.M)
    return f,f"/{d.group(1)}/{d.group(2)}/{sl.group(1)}/"
T={
"ethiopian-ful-mudammas-recipe":("Ethiopian Ful with Berbere",[("chard-with-berbere","Another Ethiopian side to serve with it:"),("whole-bean-ful-medames","Egyptian-style, with whole beans:"),("recipe-cranberr","Made with cranberry beans:"),("mesir-wat","More Ethiopian:"),("eat-ethiopian-tonight","Seattle Ethiopian recommendations:")]),
"quick-green-apple-kimchi-recipe":("Quick Green Apple Kimchi",[("making-your-own-kimchi","If you want the real fermented thing:"),("three-easy-banchan","More easy banchan:"),("tomato-and-nectarine-salad","Also made with gochugaru:")]),
"lemony-grilled-gai-lan-chinese-broccoli-recipe":("Lemony Grilled Gai Lan (Chinese Broccoli)",[("cavatelli-with-slow-roasted-broccoli","More ways to cook broccoli:"),("pan-roasted-brussels-sprouts","Another vegetable cooked hard and fast:"),("chermoula","The sauce that inspired this dish:")]),
"seared-watermelon-with-flavors-of-summer-yes-thats-vegetarian-recipe":("Seared Watermelon",[("healthy-thai-style-salad-of-grilled-eggplant","More watermelon:"),("compressed-cucumber","Another modern technique for melon:"),("watermelon-radish","Not the same melon, but fun:")]),
"pretzel-ice-cream-recipe":("Pretzel Ice Cream",[("pear-caramel-ice-cream","More homemade ice cream:"),("roasted-pumpkin-ice-cream","Another unusual ice cream:"),("you-have-mousse","Chocolate ice cream trick:"),("caramelized-raisin","Sundae sauce idea:")]),
"jalapeno-sorghum-butter-recipe":("Jalapeño-Sorghum Butter",[("best-cornbread-ever","The cornbread to put it on:"),("southernstyle-collard","A Southern meal to go with it:"),("recipe-veggie-chili","More cornbread:")]),
"stir-fried-winged-beans-kacang-botol-with-tomato-and-garlic-recipe":("Winged Bean (Kacang Botol) Stir-Fry",[("vietnamese-lemongrass-green-beans","Similar stir-fry method:"),("sichuan-dry-fried-green-beans","Another green bean stir-fry:")]),
}
n=0
for tgt,(title,srcs) in T.items():
    t=info(tgt[:30]); 
    if not t: print('MISSING target',tgt); continue
    link=t[1]
    for pre,lead in srcs:
        i=info(pre)
        if not i: print('  no source',pre); continue
        f,_=i
        s=open(f).read()
        if link in s: continue
        s=s.rstrip('\n')+f'\n\n<p class="related-link">{lead} <a href="{link}">{title}</a>.</p>\n'
        open(f,'w').write(s); n+=1; print('linked',f[:50],'->',tgt[:30])
print(n,'links added')
