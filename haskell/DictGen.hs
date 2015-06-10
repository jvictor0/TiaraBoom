module DictGen where

import Data.List
import Data.Char
import qualified Data.Map as Map
import qualified Data.Set as Set

data CapLet = A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R | S | T | U | V | W | X | Y | Z
            deriving (Show, Eq, Enum, Read)

a = 'a' 
b = 'b' 
c = 'c' 
d = 'd' 
e = 'e' 
f = 'f' 
g = 'g' 
h = 'h' 
i = 'i' 
j = 'j' 
k = 'k' 
l = 'l' 
m = 'm' 
n = 'n' 
o = 'o' 
p = 'p' 
q = 'q' 
r = 'r' 
s = 's' 
t = 't' 
u = 'u' 
v = 'v'  
w = 'w' 
x = 'x' 
y = 'y' 
z = 'z'

type DictEntry = (String,CapLet,Char,Char)

crop x = reverse $ dropWhile isSpace $ reverse x

splitComma (',':rst) = []:(splitComma rst)
splitComma (a:rst) = let (r:res) = (splitComma rst) in (a:r):res
splitComma [] = [[]]

readDE :: [String] -> String -> [DictEntry]
readDE sw str 
  | (map toLower str)`elem`sw = [] 
  | otherwise = map (\pos -> (crop $ take 23 str, 
                              read [head pos], 
                              pos!!1, pos!!2))
                poses
  where poses = splitComma $ take 23 $ drop 46 str
        
readDict :: IO [DictEntry]
readDict = do
  sw <- fmap lines $ readFile "stopwords"
  f <- fmap lines $ readFile "dict.txt"
  preresult <- return 
    $ concatMap (\poses -> filter (\(_,_,_,r) -> r == (maximum $ map (\(_,_,_,r) -> r) poses)) poses)
    $ groupBy (\(a,_,_,_) (b,_,_,_) -> a == b)
    $ concatMap (readDE sw) f
  let keyset = Set.fromList $ map (\(x,_,_,_) -> map toLower x) preresult
  names <- fmap (filter (\x -> not $ Set.member x keyset) 
                 . map (map toLower) 
                 . lines) 
           $ readFile "names.txt"
  let namesEntries = map (\(a:as) -> (a:(map toLower as),N,'n','%')) names
  return $ preresult ++ namesEntries

  
char x = head $ show x
  
realAdverb x = "yl" == (take 2 $ reverse x)
         
entries (word,M,a,b) = (entries (word,K,a,b)) ++ (entries (word,L,a,b))
entries (word,J,a,b) = (entries (word,H,a,b)) ++ (entries (word,I,a,b))
entries (word,nn,'0',_) = [(word,[char nn,t]),(word++"s",[char nn,f,a]),(word++"ing",[char nn,f,b]),(word++"ed",[char nn,f,c])]
entries (word,nn,'1',_) = [(word,[char nn,t]),(word++"es",[char nn,f,a]),(word++"ing",[char nn,f,b]),(word++"ed",[char nn,f,c])]
entries (word,nn,'2',_) = [(word,[char nn,t]),(word++"s",[char nn,f,a]),((init word)++"ing",[char nn,f,b]),(word++"d",[char nn,f,c])]
entries (word,nn,'3',_) = [(word,[char nn,t]),((init word)++"ies",[char nn,f,a]),((init word)++"ying",[char nn,f,b]),((init word)++"ied",[char nn,f,c])]
entries (word,nn,'4',_) = [(word,[char nn,t]),(word++"s",[char nn,f,a]),(word++[last word]++"ing",[char nn,f,b]),(word++[last word]++"ed",[char nn,f,c])]
entries (word,nn,'5',_) = [(word,[char nn,t])]
entries (word,nn,'6',_) = [(word,[char nn,t]),(word++"s",[char nn,f])]
entries (word,nn,'7',_) = [(word,[char nn,t]),(word++"es",[char nn,f])]
entries (word,nn,'8',_) = [(word,[char nn,t]),((init word)++"ies",[char nn,f])]
entries (word,nn,'9',_) = [(word,[char nn,t]),(word,[char nn,f])]
entries (word,nn,'@',_) = [(word,[char nn,t])]
entries (word,nn,'A',_) = [(word,[char nn,t])]
entries (word,nn,'B',_) = [(word,[char nn,t]),(word++"r",[char nn,f,r]),(word++"st",[char nn,f,s])]
entries (word,nn,'C',_) = [(word,[char nn,t]),(word++"er",[char nn,f,r]),(word++"est",[char nn,f,s])]
entries (word,nn,'D',_) = [(word,[char nn,t]),((init word)++"ier",[char nn,f,r]),((init word)++"est",[char nn,f,s])]
entries (word,nn,'E',_) = [(word,[char nn,t])]
entries (word,nn,nc,_) 
  | nc`elem`"abcdrs"      = [(word,[char nn,f,nc])]
entries (word,nn,nc,_) 
  | nc`elem`"efghpqt"      = []
entries (word,nn,'i',_) = [(word,[char nn,t])]
entries (word,nn,'j',_) = [(word,[char nn,f])]
entries (word,nn,'k',_) = [(word,[char nn,t])]
entries (word,N,lmno,_) = [(word,[char N,lmno])]
entries (word,P,tp,_) 
  | realAdverb word = [(word,[char P,tp])]
entries _ = []

entries_base (word,a,b,c) = filter (\(w,_) -> w == word) $ entries (word,a,b,c)

insertBaseDict :: Map.Map String [String] -> DictEntry -> Map.Map String [String]
insertBaseDict mp de
  | entries de == [] = mp
insertBaseDict mp de = let es@((w,rst):_) = entries_base de
                       in Map.insertWith (++) w (map snd es) mp
                      
englishDict = fmap (foldl' insertBaseDict Map.empty) readDict
 
insertIdeas :: Map.Map String [(String,String)] -> DictEntry -> Map.Map String [(String,String)]
insertIdeas mp de = let es = entries de
                    in foldl' (\mp (w,_) -> Map.insertWith (++) (map toLower w) es mp) mp es

ideas = do
  is <- fmap (fmap nub . foldl' insertIdeas Map.empty) readDict
  sw <- fmap lines $ readFile "stopwords"
  return $ Map.fromList $ map (\(a,b) -> (map toLower a,b)) $ Map.toList 
    $ unionFind 
    $ fmap (map fst)
    $ Map.filterWithKey (\k _ -> k`notElem`sw) $ Map.filter (not . null) 
    $ fmap (\l -> let len = length l in filter (\(_,x) -> (len == 1) || x /= "Nl") l)
    $ fmap (filter ((`notElem`sw).(map toLower).fst)) is
  
families = do
  is <- ideas
  return $ Map.fromList $ concatMap (\(k,v) -> map (flip (,) k . map toLower) v) $ Map.toList is
  
lookupOrEmpty x mp = case Map.lookup x mp of
  Nothing -> []
  (Just a) -> a
  
type UnionFind a = Map.Map a a

uf_insert a uf = snd $ uf_find a uf

uf_find :: (Ord a) => a -> UnionFind a -> (a,UnionFind a)
uf_find s uf = case Map.lookup s uf of
  Nothing -> (s,Map.insert s s uf)
  (Just f') -> if f' == s 
               then (s,uf) 
               else let (f,uf') = uf_find f' uf in (f, Map.insert s f uf')

uf_union :: (Ord a) => a -> a -> UnionFind a -> UnionFind a
uf_union a b uf = let (c,uf') = uf_find a uf
                      (c',uf'') = uf_find b uf'
                  in if c == c' then uf'' else Map.insert c c' uf''
                  
uf_unions :: (Ord a) => [a] -> UnionFind a -> UnionFind a
uf_unions as uf = let a = head as in foldl' (\uf b -> uf_union a b uf) (uf_insert a uf) $ tail as

uf_subsets :: (Ord a) => UnionFind a -> Map.Map a [a]
uf_subsets uf = foldl' (\mp a -> Map.insertWith (++) (fst $ uf_find a uf) [a] mp) Map.empty $ Map.keys uf

unionFind :: (Ord a) => Map.Map a [a] -> Map.Map a [a]
unionFind ideas = uf_subsets $ foldl' (flip uf_unions) Map.empty $ Map.elems ideas

ideasString = do
  is <- ideas
  let stris = map (\(w,l) -> (show w) ++ " : " ++ (show $ l)
                             ++ (concatMap (\w' -> "," ++ (show $ map toLower w') ++ " : " ++ (show w)) 
                                 $ nub $ filter ((/= w).(map toLower)) l))
              $ Map.toList is
  return $ "{" ++ (concat $ intersperse "," stris )++ "}" 
  
dictString = do
  ed <- englishDict
  return $ "{" ++ (concat $ intersperse "," $ map (\(a,bs) -> (show a) ++ " : " 
                                                             ++ (show $ map (\b -> "(" ++ b ++ ")") bs))
                  $ Map.toList ed) ++ "}"
  
saveIdeas = do
  str <- ideasString
  dict_str <- dictString
  writeFile "../data/english_families.json" str
  writeFile "../data/english_pos.json" dict_str
