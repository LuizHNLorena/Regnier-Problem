#coding: utf-8
import csv
import time
from igraph import Graph

class RegnierProblemLP:

    """Regnier Problem Class
    
    Clustering qualitative data through Integer Linear Programming.

    Attributes:
        S (list of list of int): Similarity Matrix
        n (int): Number of instances
        m (int): Number of attributes

    """
 
    def __init__(self,dataset): 
        """Receives dataset name and construct Similarity Matrix

        It receives as parameter the path to the dataset. The dataset is 
        stored temporaly in matrix 'D', while its dimensions are store in 'n'
        and 'm'.
        
        A Similarity Matrix 'S', with size (nxn) is constructed using the simetric difference 
        between each element.

        Missing values '?' are compensated when calculating the simetric difference

        Args:
            dataset (str): The path to the dataset file. 

        """
        
        self.__S=[]
        self.__n=0
        self.__m=0

        # Store dataset files in matrix 'D' and get 'n' and 'm' values
        D=[]
        with open(dataset, 'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in spamreader:
                D.append([])
                for v in row:
                    D[self.__n].append(v)
                    self.__m = self.__m + 1
                self.__n = self.__n + 1
            self.__m=self.__m//self.__n

        # Create similarity matrix. Initializing it with -m-1 in the lower triangle of matrix 'S'
        for i in range(self.__n):
            self.__S.append([])
            for j in range (self.__n):
                self.__S[i].append(-self.__m -1)

        # Calculate the simetric difference between each instance and store it in 'S'. 
        # The (-) negates the distance, transforming it into a similarity measure.
        # Missing values "?" are ignored in the similarity calculus.
        for i in range(self.__n):
            for j in range (self.__n):
                if i != j:
                    total = 0
                    total_missing = 0
                    for k in range(self.__m):
                        if D[i][k] != "?" and D[j][k] != "?":
                            if D[i][k] == D[j][k]:
                                total = total + 1
                        else:
                            total_missing = total_missing + 1
                    self.__S[i][j] = -((self.__m - total_missing) - 2*(total))
    
    def saveRM(self,filename,lp_problem=False):
        """"Save Original Model (RM)

        Save the original model of Regnier Problem in LP file format.
        
        Args:
            filename (str): The path to save the LP file. 
            lp_problem (bool,optional): If True save it as Linear Programming instead of ILP.

        Returns:
            Nothing.
        
        """

        # Create LP
        print ("Creating Model file...")
        filename = filename + "(RM).lp"
        f = open(filename, 'w')
        f.write("\ENCODING=ISO-8859-1\n")
        f.write("\Problem name: RM model\n\n")
        f.write("Maximize\n")
        f.write(" obj: \n")
        total = 0
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                if total == 4:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    total = 0
                else:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                total = total + 1
                
        # Insert Constraints            
        f.write("\nSubject To\n")
        contraintID = 1
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                for k in range(j+1,self.__n):
                    # dij + djk  - dik <= 1
                    constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" - v."+str(i)+"."+str(k)+" <= 1\n")
                    f.write("%s" % constraint)
                    contraintID = contraintID + 1
                    # dij - djk  + dik <= 1
                    constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" - v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                    f.write("%s" % constraint)
                    contraintID = contraintID + 1
                    # -dij  + djk  + dik <= 1
                    constraint = (" c" +str(contraintID) + ": - v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                    f.write("%s" % constraint)
                    contraintID = contraintID + 1

        # Variables bounds
        f.write("\nBounds\n")
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                bounds = (" 0 <= v."+str(i)+"."+str(j)+" <= 1\n")
                f.write("%s" % bounds)

        # If ILP define variables as binaries
        if(lp_problem==False):
            f.write("\nBinaries\n")
            total = 0
            var_name = ""
            for i in range(self.__n):
                for j in range(i+1,self.__n):
                    total = total + 1
                    if total == 4:
                        var_name = var_name + (" v."+str(i)+"."+str(j)+"\n")
                        f.write("%s" % var_name)
                        total = 0
                        var_name = ""
                    else:
                        var_name = var_name + (" v."+str(i)+"."+str(j))
        f.write("End\n")
        f.close()
        print("Model file created.")

    def saveRMalpha(self,filename,lp_problem=False):
        """"Save Alpha Model (RMalpha0)

        Save the Alpha model proposed by Miyauchi and Sukegawa[1] in LP file format.

        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.

        Args:
            filename (str): The path to save the LP file. 
            lp_problem (bool,optional): If True save it as Linear Programming instead of ILP.

        Returns:
            Nothing.
        
        """

        cut = 0

        # Create LP
        print ("Creating Model file...")
        filename = filename + "(RMalpha0).lp"
        f = open(filename, 'w')
        f.write("\ENCODING=ISO-8859-1\n")
        f.write("\Problem name: RMalpha0 model\n\n")
        f.write("Maximize\n")
        f.write(" obj: \n")
        total = 0
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                if total == 4:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    total = 0
                else:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                total = total + 1
                
        # Insert Constraints            
        f.write("\nSubject To\n")
        contraintID = 1
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                for k in range(j+1,self.__n):
                    # dij + djk  - dik <= 1
                    if (self.__S[i][j] >= cut or self.__S[j][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" - v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # dij - djk  + dik <= 1
                    if (self.__S[i][j] >= cut or self.__S[i][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" - v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # -dij  + djk  + dik <= 1
                    if (self.__S[j][k] >= cut or self.__S[i][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": - v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1

        f.write("Bounds\n")
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                bounds = (" 0 <= v."+str(i)+"."+str(j)+" <= 1\n")
                f.write("%s" % bounds)

        if(lp_problem==False):
            f.write("Binaries\n")
            total = 0
            var_name = ""
            for i in range(self.__n):
                for j in range(i+1,self.__n):
                    total = total + 1
                    if total == 4:
                        var_name = var_name + (" v."+str(i)+"."+str(j)+"\n")
                        f.write("%s" % var_name)
                        total = 0
                        var_name = ""
                    else:
                        var_name = var_name + (" v."+str(i)+"."+str(j))
        f.write("End\n")
        f.close()
        print("Model file created.")

    def saveRMalphaPlus(self,filename,lp_problem=False,debug=False):
        """"Save Alpha Plus Model (RMalpha+)

        Save the Alpha Plus model proposed as extension to the (RMalpha) proposed by Miyauchi and Sukegawa[1].
        
        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.

        Args:
            filename (str): The path to save the LP file. 
            lp_problem (bool,optional): If True save it as Linear Programming instead of ILP.
            debug (bool,optional): If True shows heuristic debug information.

        Returns:
            Nothing.
        
        """

        heuristic = self.__findPositiveCut(debug=debug)
        cut = heuristic['cut']

        # Create LP
        print ("Creating Model file...")
        filename = filename + "(RMalpha+).lp"
        f = open(filename, 'w')
        f.write("\ENCODING=ISO-8859-1\n")
        f.write("\Problem name: RMalpha+ model\n\n")
        f.write("Maximize\n")
        f.write(" obj: \n")
        total = 0
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                if total == 4:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    total = 0
                else:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                total = total + 1
                
        # Insert Constraints            
        f.write("\nSubject To\n")
        contraintID = 1
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                for k in range(j+1,self.__n):
                    # dij + djk  - dik <= 1
                    if (self.__S[i][j] >= cut or self.__S[j][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" - v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # dij - djk  + dik <= 1
                    if (self.__S[i][j] >= cut or self.__S[i][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" - v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # -dij  + djk  + dik <= 1
                    if (self.__S[j][k] >= cut or self.__S[i][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": - v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1

        f.write("Bounds\n")
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                bounds = (" 0 <= v."+str(i)+"."+str(j)+" <= 1\n")
                f.write("%s" % bounds)

        if(lp_problem==False):
            f.write("Binaries\n")
            total = 0
            var_name = ""
            for i in range(self.__n):
                for j in range(i+1,self.__n):
                    total = total + 1
                    if total == 4:
                        var_name = var_name + (" v."+str(i)+"."+str(j)+"\n")
                        f.write("%s" % var_name)
                        total = 0
                        var_name = ""
                    else:
                        var_name = var_name + (" v."+str(i)+"."+str(j))
        f.write("End\n")
        f.close()
        print("Model file created.")
    
    def saveRMbeta(self,filename,lp_problem=False):
        """"Save Beta Model (RMbeta0)

        Save the Beta model proposed by Miyauchi and Sukegawa[1] in LP file format.

        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.

        Args:
            filename (str): The path to save the LP file. 
            lp_problem (bool,optional): If True save it as Linear Programming instead of ILP.

        Returns:
            Nothing.
        
        """

        cut = 0

        # Create LP
        print ("Creating Model file...")
        filename = filename + "(RMbeta0).lp"
        f = open(filename, 'w')
        f.write("\ENCODING=ISO-8859-1\n")
        f.write("\Problem name: RMbeta model\n\n")
        f.write("Maximize\n")
        f.write(" obj: \n")
        total = 0
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                if total == 4:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    total = 0
                else:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                total = total + 1
                
        # Insert Constraints            
        f.write("\nSubject To\n")
        contraintID = 1
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                for k in range(j+1,self.__n):
                    # dij + djk  - dik <= 1
                    if (self.__S[i][j] + self.__S[j][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" - v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # dij - djk  + dik <= 1
                    if (self.__S[i][j] + self.__S[i][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" - v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # -dij  + djk  + dik <= 1
                    if (self.__S[j][k] + self.__S[i][k] >= cut): 
                        constraint = (" c" +str(contraintID) + ": - v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1

        f.write("Bounds\n")
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                bounds = (" 0 <= v."+str(i)+"."+str(j)+" <= 1\n")
                f.write("%s" % bounds)

        if(lp_problem==False):
            f.write("Binaries\n")
            total = 0
            var_name = ""
            for i in range(self.__n):
                for j in range(i+1,self.__n):
                    total = total + 1
                    if total == 4:
                        var_name = var_name + (" v."+str(i)+"."+str(j)+"\n")
                        f.write("%s" % var_name)
                        total = 0
                        var_name = ""
                    else:
                        var_name = var_name + (" v."+str(i)+"."+str(j))
        f.write("End\n")
        f.close()
        print("Model file created.")

    def saveRMbetaPlus(self,filename,lp_problem=False,debug=False):
        """"Save Beta Plus Model (RMbeta+)

        Save the Beta Plus model proposed as extension to the (RMbeta) proposed by Miyauchi and Sukegawa[1].
        
        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.

        Args:
            filename (str): The path to save the LP file. 
            lp_problem (bool,optional): If True save it as Linear Programming instead of ILP.
            debug (bool,optional): If True shows heuristic debug information.

        Returns:
            Nothing.
        
        """
        
        heuristic = self.__findPositiveCut(debug=debug)
        cut = heuristic['cut']

        # Create LP
        print ("Creating Model file...")
        filename = filename + "(RMbeta+).lp"
        f = open(filename, 'w')
        f.write("\ENCODING=ISO-8859-1\n")
        f.write("\Problem name: RMbeta+ model\n\n")
        f.write("Maximize\n")
        f.write(" obj: \n")
        total = 0
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                if total == 4:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    total = 0
                else:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                total = total + 1
                
        # Insert Constraints            
        f.write("\nSubject To\n")
        contraintID = 1
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                for k in range(j+1,self.__n):
                    # dij + djk  - dik <= 1
                    if (self.__S[i][j] + self.__S[j][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" - v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # dij - djk  + dik <= 1
                    if (self.__S[i][j] + self.__S[i][k] >= cut):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" - v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # -dij  + djk  + dik <= 1
                    if (self.__S[j][k] + self.__S[i][k] >= cut): 
                        constraint = (" c" +str(contraintID) + ": - v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1

        f.write("Bounds\n")
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                bounds = (" 0 <= v."+str(i)+"."+str(j)+" <= 1\n")
                f.write("%s" % bounds)

        if(lp_problem==False):
            f.write("Binaries\n")
            total = 0
            var_name = ""
            for i in range(self.__n):
                for j in range(i+1,self.__n):
                    total = total + 1
                    if total == 4:
                        var_name = var_name + (" v."+str(i)+"."+str(j)+"\n")
                        f.write("%s" % var_name)
                        total = 0
                        var_name = ""
                    else:
                        var_name = var_name + (" v."+str(i)+"."+str(j))
        f.write("End\n")
        f.close()
        print("Model file created.")

    def saveRMgamma(self,filename,lp_problem=False,debug=False):
        """"Save Gamma Model (RMgamma)

        Save the Gamma model proposed to extend the models proposed by Miyauchi and Sukegawa[1].
        
        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.

        Args:
            filename (str): The path to save the LP file. 
            lp_problem (bool,optional): If True save it as Linear Programming instead of ILP.
            debug (bool,optional): If True shows heuristic debug information.

        Returns:
            Nothing.
        
        """

        # Calculate best gamma
        heuristic = self.__findNegativeCut(debug=debug)
        gamma = heuristic['cut']

        # Create LP
        print ("Creating Model file...")
        filename = filename + "(RMgamma).lp"
        f = open(filename, 'w')
        f.write("\ENCODING=ISO-8859-1\n")
        f.write("\Problem name: RMgamma model\n\n")
        f.write("Maximize\n")
        f.write(" obj: \n")
        total = 0
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                if total == 4:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j)+" \n")
                        f.write("%s" % var_name)
                    total = 0
                else:
                    if self.__S[i][j] >= 0:
                        var_name = (" + " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                    else:
                        var_name = (" - " + str(abs(self.__S[i][j])) + " v."+str(i)+"."+str(j))
                        f.write("%s" % var_name)
                total = total + 1
                
        # Insert Constraints            
        f.write("\nSubject To\n")
        contraintID = 1
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                for k in range(j+1,self.__n):
                    # dij + djk  - dik <= 1
                    if (self.__S[i][j] >= 0 and self.__S[j][k] >= gamma and self.__S[i][k] <= 0):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" - v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # dij - djk  + dik <= 1
                    if (self.__S[i][j] >= 0 and self.__S[j][k] <= 0 and self.__S[i][k] >= gamma):
                        constraint = (" c" +str(contraintID) + ": v."+str(i)+"."+str(j)+" - v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1
                    # -dij  + djk  + dik <= 1
                    if (self.__S[i][j] <= 0 and self.__S[j][k] >= gamma and self.__S[i][k] >= 0):
                        constraint = (" c" +str(contraintID) + ": - v."+str(i)+"."+str(j)+" + v."+str(j)+"."+str(k)+" + v."+str(i)+"."+str(k)+" <= 1\n")
                        f.write("%s" % constraint)
                        contraintID = contraintID + 1

        f.write("Bounds\n")
        for i in range(self.__n):
            for j in range(i+1,self.__n):
                bounds = (" 0 <= v."+str(i)+"."+str(j)+" <= 1\n")
                f.write("%s" % bounds)

        if(lp_problem==False):
            f.write("Binaries\n")
            total = 0
            var_name = ""
            for i in range(self.__n):
                for j in range(i+1,self.__n):
                    total = total + 1
                    if total == 4:
                        var_name = var_name + (" v."+str(i)+"."+str(j)+"\n")
                        f.write("%s" % var_name)
                        total = 0
                        var_name = ""
                    else:
                        var_name = var_name + (" v."+str(i)+"."+str(j))
        f.write("End\n")
        f.close()
        print("Model file created.")

    def __findPositiveCut(self,debug=False):
        """Best positive cut heuristic.

        Heuristic to find the best cut value to construct the Alpha Plus Model (RMalpha+).

        Args:
            debug (bool,optional): Show debug information. 

        Returns:
            A Heuristic object that contains all the relevant info about the heuristic.
        
        """

        time_total = time.time()
        
        # Graph and unique set construction
        time_graph_construction = time.time()

        graph_positive = Graph()
        graph_positive.add_vertices(self.__n)
        unique_positive_weights = set()
        for i in range(self.__n):
            for j in range (i+1,self.__n):
                if self.__S[i][j] >= 0:
                    graph_positive.add_edge(i,j,weight=self.__S[i][j])
                    unique_positive_weights.add(self.__S[i][j])
        
        time_graph_construction = time.time() - time_graph_construction

        # Sort unique weights and start heuristic to find the best cut value
        time_find_best_cut = time.time()
        
        unique_positive_weights = sorted(unique_positive_weights)

        # Test different cuts and check connected
        best_positive_cut = 0
        for newCut in unique_positive_weights:
            edges_to_delete = graph_positive.es.select(weight_lt=newCut)
            graph_positive.delete_edges(edges_to_delete)
            if graph_positive.is_connected():
                best_positive_cut = newCut
            else:
                break

        time_find_best_cut = time.time() - time_find_best_cut
        time_total = time.time() - time_total

        if debug==True:
            print ("################################")
            print ("# Heuristic debug info")
            print ("################################")
            print ("Time Graph Construction: %f"         %(time_graph_construction))
            print ("Time Heuristic to find best cut: %f" %(time_find_best_cut))
            print ("Total Time: %f"                      %(time_total))
            print ("NEW (Best cut+): %d"                 %(best_positive_cut))
            print ("################################")

        heuristic={}
        heuristic['cut'] = best_positive_cut
        heuristic['time_total']=time_total
        heuristic['time_graph_construction']=time_graph_construction
        heuristic['time_find_best_cut']=time_find_best_cut

        return heuristic     

    def __findNegativeCut(self,debug=False):
        """Best negative cut heuristic.

        Heuristic to find the best cut value to construct the Gamma Model (RMgamma).

        Args:
            debug (bool,optional): Show debug information. 

        Returns:
            A Heuristic object that contains all the relevant info about the heuristic.
        
        """
        
        time_total = time.time()

        # Graph and unique set construction
        time_graph_construction = time.time()

        graph_negative = Graph()
        graph_negative.add_vertices(self.__n)
        unique_negative_weights = set()
        for i in range(self.__n):
            for j in range (i+1,self.__n):
                if self.__S[i][j] <= 0:
                    graph_negative.add_edge(i,j,weight=self.__S[i][j])
                    unique_negative_weights.add(self.__S[i][j])
        time_graph_construction = time.time() - time_graph_construction

        # Sort unique weights and start heuristic to find the best cut value
        time_find_best_cut = time.time()
        
        unique_negative_weights = sorted(unique_negative_weights)

        # Test different cuts and check connected
        best_negative_cut = 0
        for newCut in unique_negative_weights:
            edges_to_delete = graph_negative.es.select(weight_lt=newCut)
            graph_negative.delete_edges(edges_to_delete)
            if graph_negative.is_connected():
                best_negative_cut = newCut
            else:
                break

        time_find_best_cut = time.time() - time_find_best_cut
        time_total = time.time() - time_total

        if debug==True:
            print ("Time Graph Construction: %f"         %(time_graph_construction))
            print ("Time Heuristic to find best cut: %f" %(time_find_best_cut))
            print ("Total Time: %f"                      %(time_total))
            print ("NEW (Best cut-): %d"                 %(best_negative_cut))

        heuristic={}
        heuristic['cut'] = best_negative_cut
        heuristic['time_total']=time_total
        heuristic['time_graph_construction']=time_graph_construction
        heuristic['time_find_best_cut']=time_find_best_cut

        return heuristic
