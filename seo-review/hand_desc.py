import glob,re
H={
"saffron-date-posset":'Saffron-date posset: a classic English dessert of cream set with acid instead of starch or egg, so it tastes only of cream and its flavorings.',
"review-the-lege":'Review of Abulafia, the 24-hour streetside bakery in Jaffa near Tel Aviv, open since 1879, including its stuffed sambusac pastries.',
"the-vegetarian-tasting-menu-at-canlis":"A vegetarian tasting menu at Canlis, Seattle's legendary fine-dining restaurant, written by someone who staged in its kitchen in 2010.",
"stop-scraping":'Review of the BeaterBlade, a KitchenAid paddle attachment with soft edges that scrape the bowl for you, so you never have to stop the mixer.',
"how-to-use-a-sharpening":'How to use a sharpening steel on your kitchen knives, with a video demonstration of the technique.',
"the-adaptable-feast":"Review of Ivy Manning's cookbook The Adaptable Feast, plus a chance to win a copy.",
"summer-salad-amuse":'A summer salad amuse bouche of diced cucumber, peas in the pod, cherry tomato and lemon basil: a pop of gazpacho-like flavor.',
"burnt-sugar-flan":'Burnt sugar flan (crème caramel) from a Rick Bayless classic, made as one large flan that unmolds with a waterfall of caramel.',
"why-im-a-vegetarian":"Why I'm a vegetarian: a personal essay after almost 25 years of answering the question.",
"fremont-neighborhood-lunch-roundup":'A roundup of Seattle Fremont lunch spots, reviewed for their vegetarian options, with notes on atmosphere, service and price.',
"flying-squirrel-pizza":'Review of Flying Squirrel Pizza Company in Seattle, including the #8 pie with free-range egg, buffalo mozzarella, arugula and red onion.',
"tea-smoked-lych":'Fresh lychee smoked with genmaicha tea, the first of three lychee amuse bouche that also work as an appetizer trio.',
"quesadilla":'The trick for crispy corn tortilla quesadillas: brush both sides with oil. Recipe with pecorino and onion and garlic jam.',
"spicy-mama-lils-spaghetti-carbonara":'Spicy vegetarian spaghetti alla carbonara in video: watch the crucial step of tossing the hot pasta with the eggs.',
"gomashio":'Gomashio, the Japanese sesame seed and salt condiment. Simple to make at home and delicious.',
"zucchini-chickpea-tagine":'Zucchini and chickpea tagine recipe, plus what a tagine is: the Moroccan clay pot and the slow-braised dishes cooked in it.',
"recipe-vietname":'Vegetarian banh mi chay recipe: Vietnamese sandwiches made with tofu.',
"quick-chana-mushroom-masala":'Quick chana masala with mushrooms, a spicy chickpea curry, one of the dishes found at nearly every Indian restaurant in America.',
"experimenting-with-tapioca-maltodextrin":'Experiments with tapioca maltodextrin, a modern-cuisine ingredient, in a home kitchen.',
"the-dirt-candy-cookbook-review":'Review of the Dirt Candy cookbook by chef Amanda Cohen.',
"what-i-learned-staging-at-canlis":"What I learned staging at Canlis, Seattle's legendary fine-dining restaurant, during a couple of weeks in its kitchen.",
"vegetarian-bibimbap":"Vegetarian bibimbap, the Korean rice bowl with seasoned vegetables, egg and gochujang sauce. A favorite Korean dish made meat-free.",
"latkes-crispy-for-hannukah":"How to make crispy potato latkes for Hanukkah with just potato, onion, egg and salt. Tips for getting them shatteringly crisp.",
}
n=0
for f in glob.glob('content/posts/*.md'):
    sl=f.split('/')[-1][:-3]
    k=next((k for k in H if sl.startswith(k)),None)
    if not k: continue
    s=open(f).read(); head,rest=s.split('\n---\n',1)
    q='"'+H[k].replace('"','\\"')+'"'
    head=re.sub(r'^description:.*\n?','',head,flags=re.M)
    head=re.sub(r'^(title:.*)$',lambda m:m.group(1)+f'\ndescription: {q}',head,count=1,flags=re.M)
    open(f,'w').write(head+'\n---\n'+rest); n+=1; assert len(H[k])<=165,(k,len(H[k]))
print(n,'hand-written')
