import csv, json, re, datetime as dt
R = {r['Title']: r for r in csv.DictReader(open('/tmp/pins_b3.csv'))}
slugs = json.load(open('/tmp/b3slugs.json'))
KW = {
 'vegetarian-gravy-guess-the-secret-ingredient-recipe':'vegetarian gravy,thanksgiving gravy,vegan gravy,mushroom gravy,holiday sides',
 'potato-and-fennel-gratin-recipe':'potato gratin,fennel gratin,thanksgiving side dish,holiday sides,vegetarian side dishes',
 'brusels-sprout-and-apple-hash-recipe':'brussels sprouts,brussels sprout hash,apple side dish,thanksgiving sides,fall vegetables',
 'recipe-delicata':'stuffed delicata squash,delicata squash recipes,vegetarian thanksgiving,orzo stuffing,fall dinner',
 'red-lentil-and-kabocha-squash-soup-with-harissa-oil-sneak-peak-recipe-from-the-cookbook':'red lentil soup,kabocha squash soup,harissa oil,vegan soup,winter soup',
 'recipe-cranberr':'cranberry beans,borlotti beans,ful mudammas,vegetarian bean recipes,egyptian beans',
 'kala-chana-black-chickpea-curry':'kala chana,black chickpea curry,indian vegetarian,chickpea curry,vegan indian',
 'khao-soi-thai-curry-noodles-from-chiang-mai':'khao soi,thai curry noodles,vegetarian khao soi,coconut curry noodles,thai noodle soup',
 'mandu-koreanstyle-potstickers-with-ssamjang-kochujang-sauce-recipe':'mandu,korean dumplings,vegetarian potstickers,ssamjang,korean appetizer',
 'vegetarian-bibimbap-korean-rice-with-vegetables-and-kochujang-recipe':'vegetarian bibimbap,korean rice bowl,gochujang,korean vegetarian,rice bowl recipes',
 'quick-chana-mushroom-masala-chickpea-curry-recipe':'chana masala,chickpea curry,mushroom curry,indian vegetarian,quick vegetarian dinner',
 'enchiladas-de-mole-recipe':'mole enchiladas,vegetarian enchiladas,mushroom enchiladas,mexican vegetarian,mole sauce',
 'kimchi-fried-rice-kimchi-bokkeumbap-recipe':'kimchi fried rice,kimchi bokkeumbap,korean fried rice,vegetarian fried rice,kimchi recipes',
 'chickpea-and-potato-stew-with-baharat-recipe':'chickpea stew,turkish chickpea stew,baharat,vegan stew,potato chickpea stew',
}
files={}
import glob,os
for f in glob.glob('../site/content/posts/*.md'): files[os.path.basename(f)[:-3]]=f
rows=[]
start=dt.datetime(2026,11,16,21,0)   # 21:00 UTC = 1 PM PST, third daily slot
for i,s in enumerate(slugs):
    r=next(v for v in R.values() if v['Media URL'].endswith('/'+s+'.jpg'))
    fm=open(files[s]).read().split('---')[1]
    d=re.search(r'^description:\s*"(.*)"\s*$',fm,re.M).group(1).replace('\\"','"')
    if len(d)>260: d=d[:257].rsplit(' ',1)[0]+'…'
    OV={'khao-soi-thai-curry-noodles-from-chiang-mai':"Khao soi, the Thai curry noodle soup from Chiang Mai, made vegetarian with tofu in a rich coconut curry broth and topped with crispy fried noodles.",
        'recipe-cranberr':"Cranberry (borlotti) beans cooked fool mudammas-style, the Egyptian way, as a hearty vegetarian bean dish with big flavor."}
    desc=OV.get(s,d)+' Get the full vegetarian recipe at herbivoracious.com.'
    rows.append({"Title":r["Title"].replace('\\"','"')[:100],"Media URL":r["Media URL"],"Pinterest board":r["Pinterest board"],"Thumbnail":"","Description":desc,"Link":r["Link"],"Publish date":(start+dt.timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S"),"Keywords":KW[s]})
with open('batch3.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=["Title","Media URL","Pinterest board","Thumbnail","Description","Link","Publish date","Keywords"]); w.writeheader(); w.writerows(rows)
for r in rows: print(r["Publish date"],r["Pinterest board"][:20],'|',r["Title"][:50],'|',r["Description"][:90])
