#coding: utf-8
import cplex
from cplex.exceptions import CplexError
import csv
import time
from igraph import Graph

class RegnierProblem:

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
        
        self._S=[]
        self._n=0
        self._m=0

        # Store dataset files in matrix 'D' and get 'n' and 'm' values
        D=[]
        with open(dataset, 'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in spamreader:
                D.append([])
                for v in row:
                    D[self._n].append(v)
                    self._m = self._m + 1
                self._n = self._n + 1
            self._m=self._m//self._n

        # Create similarity matrix. Initializing it with -m-1 in the lower triangle of matrix 'S'
        for i in range(self._n):
            self._S.append([])
            for j in range (self._n):
                self._S[i].append(-self._m -1)

        # Calculate the simetric difference between each instance and store it in 'S'. 
        # The (-) negates the distance, transforming it into a similarity measure.
        # Missing values "?" are ignored in the similarity calculus.
        for i in range(self._n):
            for j in range (self._n):
                if i != j:
                    total = 0
                    total_missing = 0
                    for k in range(self._m):
                        if D[i][k] != "?" and D[j][k] != "?":
                            if D[i][k] == D[j][k]:
                                total = total + 1
                        else:
                            total_missing = total_missing + 1
                    self._S[i][j] = -((self._m - total_missing) - 2*(total))
        
    def runRM(self,lp_problem=False,debug=False,model_file=None):
        """Original Model (RM)

        Creates the original model of Regnier Problem and runs in CPLEX.
        
        Args:
            lp_problem (bool,optional): If True run as Linear Programming instead of ILP.
            debug (bool,optional): Show debug information, mostly CPLEX output.
            model_file (str,optional): Save the model to .lp format file.

        Returns:
            A Solution object.
        
        """
        
        solution = None

        ############################
        # Create IP Model
        ##############################
        try:
            # Create cplex instance
            my_prob = cplex.Cplex()

            if not debug:
                # Disable cplex output
                my_prob.set_log_stream(None)
                my_prob.set_error_stream(None)
                my_prob.set_warning_stream(None)
                my_prob.set_results_stream(None)
            
            # Define it as a maximization problem
            my_prob.objective.set_sense(my_prob.objective.sense.maximize)

            # Variables matrix
            X=[]
            for i in range(self._n):
                X.append([])
                for j in range(self._n):
                    X[i].append(0)

            # Create Objective Function
            if lp_problem==True:
                for i in range(self._n):
                    for j in range(i+1,self._n):
                        var_name = "v."+str(i)+"."+str(j)
                        X[i][j] = my_prob.variables.get_num()
                        my_prob.variables.add(obj = [self._S[i][j]], 
                                                     lb = [0], 
                                                     ub = [1], 
                                                     names = [var_name],
                                                     types = [my_prob.variables.type.continuous] )
            else:
                for i in range(self._n):
                    for j in range(i+1,self._n):
                        var_name = "v."+str(i)+"."+str(j)
                        X[i][j] = my_prob.variables.get_num()
                        my_prob.variables.add(obj = [self._S[i][j]], 
                                                     lb = [0], 
                                                     ub = [1], 
                                                     names = [var_name],
                                                     types = [my_prob.variables.type.binary] )
            
            # Insert Constraints
            for i in range(self._n):
                for j in range(i+1,self._n):
                    for k in range(j+1,self._n):
                        # Constraints
                        # dij + djk  - dki <= 1
                        the_vars  = []
                        the_coefs = []
                        the_vars.append(X[i][j])
                        the_coefs.append(1)
                        the_vars.append(X[j][k])
                        the_coefs.append(1)
                        the_vars.append(X[i][k])
                        the_coefs.append(-1)
                        my_prob.linear_constraints.add(lin_expr = \
                                                       [cplex.SparsePair(the_vars, the_coefs)],
                                                       senses = ["L"], rhs = [1])
                        # dij - djk  + dki <= 1
                        the_vars  = []
                        the_coefs = []
                        the_vars.append(X[i][j])
                        the_coefs.append(1)
                        the_vars.append(X[j][k])
                        the_coefs.append(-1)
                        the_vars.append(X[i][k])
                        the_coefs.append(1)
                        my_prob.linear_constraints.add(lin_expr = \
                                                       [cplex.SparsePair(the_vars, the_coefs)],
                                                       senses = ["L"], rhs = [1])
                        # -dij  + djk  + dki <= 1
                        the_vars  = []
                        the_coefs = []
                        the_vars.append(X[i][j])
                        the_coefs.append(-1)
                        the_vars.append(X[j][k])
                        the_coefs.append(1)
                        the_vars.append(X[i][k])
                        the_coefs.append(1)
                        my_prob.linear_constraints.add(lin_expr = \
                                                       [cplex.SparsePair(the_vars, the_coefs)],
                                                       senses = ["L"], rhs = [1])

            
            # Save model
            if(model_file != None):
                my_prob.write(model_file)
                        
            # Solve
            time_solver = my_prob.get_time()
            my_prob.solve()
            time_solver = my_prob.get_time() - time_solver

            # Number of constraints
            num_rows = my_prob.linear_constraints.get_num()

            # Number of Variables
            num_cols = my_prob.variables.get_num()

            # Objective value
            objective = my_prob.solution.get_objective_value()

            # Solution
            x = my_prob.solution.get_values()

            # Creating partition
            groups = []
            for i in range(self._n):
                groups.append(-1)

            groupID = 0
            for i in range(self._n):
                for j in range(self._n):
                    index = X[i][j]
                    if x[index] > 0:
                        # Both objects don't have group, put then together on a new
                        if groups[i] == -1 and groups[j] == -1:
                            groups[i] = groupID
                            groups[j] = groupID
                            groupID = groupID + 1
                        else:
                            # If i object don't have group put him on j group
                            if groups[i] == -1:
                                groups[i] = groups[j]
                            else:
                                groups[j] = groups[i]

            # The objects that remained alone create its own group
            for i in range(len(groups)):
                if groups[i] == -1:
                    groups[i] = groupID
                    groupID = groupID + 1
                        
            # Make solution object to return
            solution = {'num_rows':num_rows,
                        'num_cols':num_cols,
                        'objective':objective,
                        'time_solver':time_solver,
                        'heuristic':None,
                        'groups':groups}
        
        except CplexError as exc:
            print (exc)
         
        return solution

    def runRMalpha(self,cut=0,lp_problem=False,debug=False,model_file=None):
        """Alpha Model (RMalpha0)

        Creates the Alpha model proposed by Miyauchi and Sukegawa[1] and runs in CPLEX.

        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.
        
        Args:
            cut (int,optional): The default value corresponds to the model proposed by Miyauchi and Sukegawa[1].
            lp_problem (bool,optional): If True run as Linear Programming instead of ILP.
            debug (bool,optional): Show debug information, mostly CPLEX output.
            model_file (str,optional): Save the model to .lp format file.

        Returns:
            A Solution object.
        
        """

        solution = None

        ############################
        # Create IP Model
        ##############################
        ### MODELO CPLEX
        try:

            # Create cplex instance
            my_prob = cplex.Cplex()

            if debug == False:
                # Disable cplex output
                my_prob.set_log_stream(None)
                my_prob.set_error_stream(None)
                my_prob.set_warning_stream(None)
                my_prob.set_results_stream(None)

            # Define it as a maximization problem
            my_prob.objective.set_sense(my_prob.objective.sense.maximize)

            # Variables matrix
            X=[]
            for i in range(self._n):
                X.append([])
                for j in range(self._n):
                    X[i].append(0)

            # Create Objective Function
            if lp_problem==True:
                for i in range(self._n):
                    for j in range(i+1,self._n):
                        var_name = "v."+str(i)+"."+str(j)
                        X[i][j] = my_prob.variables.get_num()
                        my_prob.variables.add(obj = [self._S[i][j]], 
                                                     lb = [0], 
                                                     ub = [1], 
                                                     names = [var_name],
                                                     types = [my_prob.variables.type.continuous] )
            else:
                for i in range(self._n):
                    for j in range(i+1,self._n):
                        var_name = "v."+str(i)+"."+str(j)
                        X[i][j] = my_prob.variables.get_num()
                        my_prob.variables.add(obj = [self._S[i][j]], 
                                                     lb = [0], 
                                                     ub = [1], 
                                                     names = [var_name],
                                                     types = [my_prob.variables.type.binary] )

            # Insert Constraints
            for i in range(self._n):
                for j in range(i+1,self._n):
                    for k in range(j+1,self._n):
                        if (self._S[i][j] >= cut or self._S[j][k] >= cut):
                            # Constraints
                            # dij + djk  - dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(1)
                            the_vars.append(X[j][k])
                            the_coefs.append(1)
                            the_vars.append(X[i][k])
                            the_coefs.append(-1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])
                        if (self._S[i][j] >= cut or self._S[i][k] >= cut):        
                            # dij - djk  + dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(1)
                            the_vars.append(X[j][k])
                            the_coefs.append(-1)
                            the_vars.append(X[i][k])
                            the_coefs.append(1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])
                        if (self._S[j][k] >= cut or self._S[i][k] >= cut):
                            # -dij  + djk  + dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(-1)
                            the_vars.append(X[j][k])
                            the_coefs.append(1)
                            the_vars.append(X[i][k])
                            the_coefs.append(1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])

            # Save model
            if(model_file != None):
                my_prob.write(model_file)

            # Solve
            time_solver = my_prob.get_time()
            my_prob.solve()
            time_solver = my_prob.get_time() - time_solver
        
            # Number of constraints
            num_rows = my_prob.linear_constraints.get_num()
        
            # Number of Variaveis
            num_cols = my_prob.variables.get_num()
        
            # Objective value
            objective = my_prob.solution.get_objective_value()

            # Solution
            x = my_prob.solution.get_values()

            # Creating partition
            groups = []
            for i in range(self._n):
                groups.append(-1)

            groupID = 0
            for i in range(self._n):
                for j in range(self._n):
                    index = X[i][j]
                    if x[index] > 0:
                        # Both objects don't have group, put then together on a new
                        if groups[i] == -1 and groups[j] == -1:
                            groups[i] = groupID
                            groups[j] = groupID
                            groupID = groupID + 1
                        else:
                            # If i object don't have group put him on j group
                            if groups[i] == -1:
                                groups[i] = groups[j]
                            else:
                                groups[j] = groups[i]

            # The objects that remained alone create its own group
            for i in range(len(groups)):
                if groups[i] == -1:
                    groups[i] = groupID
                    groupID = groupID + 1

            solution = {'num_rows':num_rows,
                        'num_cols':num_cols,
                        'objective':objective,
                        'time_solver':time_solver,
                        'heuristic':None,
                        'groups':groups}
            
        except CplexError as exc:
            print (exc)

        return solution
 
    def runRMalphaPlus(self,lp_problem=False,debug=False,model_file=None):
        """Alpha Plus Model (RMalpha+)

        Creates the new model proposed as extension to the (RMalpha) proposed by Miyauchi and Sukegawa[1] and runs in CPLEX.

        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.
        
        Args:
            lp_problem (bool,optional): If True run as Linear Programming instead of ILP.
            debug (bool,optional): Show debug information, mostly CPLEX output. 
            model_file (str,optional): Save the model to .lp format file.

        Returns:
            A Solution object.
        
        """

        heuristic = self.__findPositiveCut(debug=debug)
        solution = self.runRMalpha(cut=heuristic['cut'],lp_problem=lp_problem,debug=debug,model_file=model_file)
        solution['heuristic']=heuristic

        return solution

    def runRMbeta(self,cut=0,lp_problem=False,debug=False,model_file=None):
        """Beta Model (RMbeta0)

        Creates the Beta model proposed by Miyauchi and Sukegawa[1] and runs in CPLEX.

        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.
        
        Args:
            cut(int,optional): The default value corresponds to the model proposed by Miyauchi and Sukegawa[1].
            lp_problem (bool,optional): If True run as Linear Programming instead of ILP.
            debug (bool,optional): Show debug information, mostly CPLEX output.
            model_file (str,optional): Save the model to .lp format file.

        Returns:
            A Solution object.
        
        """

        solution = None

        ############################
        # Create IP Model
        ##############################
        ### MODELO CPLEX
        try:

            # Create cplex instance
            my_prob = cplex.Cplex()

            if debug == False:
                # Disable cplex output
                my_prob.set_log_stream(None)
                my_prob.set_error_stream(None)
                my_prob.set_warning_stream(None)
                my_prob.set_results_stream(None)

            # Define it as a maximization problem
            my_prob.objective.set_sense(my_prob.objective.sense.maximize)

            # Variables matrix
            X=[]
            for i in range(self._n):
                X.append([])
                for j in range(self._n):
                    X[i].append(0)

            # Create Objective Function
            if lp_problem==True:
                for i in range(self._n):
                    for j in range(i+1,self._n):
                        var_name = "v."+str(i)+"."+str(j)
                        X[i][j] = my_prob.variables.get_num()
                        my_prob.variables.add(obj = [self._S[i][j]], 
                                                     lb = [0], 
                                                     ub = [1], 
                                                     names = [var_name],
                                                     types = [my_prob.variables.type.continuous] )
            else:
                for i in range(self._n):
                    for j in range(i+1,self._n):
                        var_name = "v."+str(i)+"."+str(j)
                        X[i][j] = my_prob.variables.get_num()
                        my_prob.variables.add(obj = [self._S[i][j]], 
                                                     lb = [0], 
                                                     ub = [1], 
                                                     names = [var_name],
                                                     types = [my_prob.variables.type.binary] )

            # Insert Constraints
            for i in range(self._n):
                for j in range(i+1,self._n):
                    for k in range(j+1,self._n):
                        if (self._S[i][j] + self._S[j][k] >= cut):
                            # Constraints
                            # dij + djk  - dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(1)
                            the_vars.append(X[j][k])
                            the_coefs.append(1)
                            the_vars.append(X[i][k])
                            the_coefs.append(-1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])
                        if (self._S[i][j] + self._S[i][k] >= cut):        
                            # dij - djk  + dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(1)
                            the_vars.append(X[j][k])
                            the_coefs.append(-1)
                            the_vars.append(X[i][k])
                            the_coefs.append(1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])
                        if (self._S[j][k] + self._S[i][k] >= cut):
                            # -dij  + djk  + dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(-1)
                            the_vars.append(X[j][k])
                            the_coefs.append(1)
                            the_vars.append(X[i][k])
                            the_coefs.append(1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])
   
            # Save model
            if(model_file != None):
                my_prob.write(model_file)
                            
            # Solve
            time_solver = my_prob.get_time()
            my_prob.solve()
            time_solver = my_prob.get_time() - time_solver
        
            # Number of constraints
            num_rows = my_prob.linear_constraints.get_num()
        
            # Number of Variaveis
            num_cols = my_prob.variables.get_num()
        
            # Objective value
            objective = my_prob.solution.get_objective_value()

            # Solution
            x = my_prob.solution.get_values()

            # Creating partition
            groups = []
            for i in range(self._n):
                groups.append(-1)

            groupID = 0
            for i in range(self._n):
                for j in range(self._n):
                    index = X[i][j]
                    if x[index] > 0:
                        # Both objects don't have group, put then together on a new
                        if groups[i] == -1 and groups[j] == -1:
                            groups[i] = groupID
                            groups[j] = groupID
                            groupID = groupID + 1
                        else:
                            # If i object don't have group put him on j group
                            if groups[i] == -1:
                                groups[i] = groups[j]
                            else:
                                groups[j] = groups[i]

            # The objects that remained alone create its own group
            for i in range(len(groups)):
                if groups[i] == -1:
                    groups[i] = groupID
                    groupID = groupID + 1

            solution = {'num_rows':num_rows,
                        'num_cols':num_cols,
                        'objective':objective,
                        'time_solver':time_solver,
                        'heuristic':None,
                        'groups':groups}
            
        except CplexError as exc:
            print (exc)

        return solution
            
    def runRMbetaPlus(self,lp_problem=False,debug=False,model_file=None):
        """Beta Plus Model (RMbeta+)

        Creates the new model proposed as extension to the (RMbeta) proposed by Miyauchi and Sukegawa[1] and runs in CPLEX.

        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.
        
        Args:
            lp_problem (bool,optional): If True run as Linear Programming instead of ILP.
            debug (bool,optional): Show debug information, mostly CPLEX output.
            model_file (str,optional): Save the model to .lp format file.

        Returns:
            A Solution object.
        
        """

        heuristic = self.__findPositiveCut(debug=debug)
        solution = self.runRMbeta(cut=heuristic['cut'],lp_problem=lp_problem,debug=debug,model_file=model_file)
        solution['heuristic']=heuristic

        return solution

    def runRMgamma(self,lp_problem=False,debug=False,model_file=None):
        """Gamma Model (RMgamma)

        Creates the Gamma model that extend the models proposed by Miyauchi and Sukegawa[1] and runs in CPLEX.

        [1] Miyauchi, Atsushi, and Noriyoshi Sukegawa. 
        "Redundant constraints in the standard formulation for the clique partitioning problem."
        Optimization Letters 9.1 (2015): 199-207.
        
        Args:
            lp_problem (bool,optional): If True run as Linear Programming instead of ILP.
            debug (bool,optional): Show debug information, mostly CPLEX output.
            model_file (str,optional): Save the model to .lp format file.

        Returns:
            A Solution object.
        
        """

        # Call heuristic to find best cut
        heuristic = self.__findNegativeCut(debug=debug)
        cut = heuristic['cut']

        solution = None

        ############################
        # Create IP Model
        ##############################
        try:
            # Create cplex instance
            my_prob = cplex.Cplex()

            if not debug:
                # Disable cplex output
                my_prob.set_log_stream(None)
                my_prob.set_error_stream(None)
                my_prob.set_warning_stream(None)
                my_prob.set_results_stream(None)
            
            # Define it as a maximization problem
            my_prob.objective.set_sense(my_prob.objective.sense.maximize)

            # Variables matrix
            X=[]
            for i in range(self._n):
                X.append([])
                for j in range(self._n):
                    X[i].append(0)

            # Create Objective Function
            if lp_problem==True:
                for i in range(self._n):
                    for j in range(i+1,self._n):
                        var_name = "v."+str(i)+"."+str(j)
                        X[i][j] = my_prob.variables.get_num()
                        my_prob.variables.add(obj = [self._S[i][j]], 
                                                     lb = [0], 
                                                     ub = [1], 
                                                     names = [var_name],
                                                     types = [my_prob.variables.type.continuous] )
            else:
                for i in range(self._n):
                    for j in range(i+1,self._n):
                        var_name = "v."+str(i)+"."+str(j)
                        X[i][j] = my_prob.variables.get_num()
                        my_prob.variables.add(obj = [self._S[i][j]], 
                                                     lb = [0], 
                                                     ub = [1], 
                                                     names = [var_name],
                                                     types = [my_prob.variables.type.binary] )
            
            # Insert Constraints
            for i in range(self._n):
                for j in range(i+1,self._n):
                    for k in range(j+1,self._n):
                        if (self._S[i][j] >= 0 and self._S[j][k] >= cut and self._S[i][k] <= 0):
                            # Constraints
                            # dij + djk  - dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(1)
                            the_vars.append(X[j][k])
                            the_coefs.append(1)
                            the_vars.append(X[i][k])
                            the_coefs.append(-1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])
                        if (self._S[i][j] >= 0 and self._S[j][k] <= 0 and self._S[i][k] >= cut):
                            # dij - djk  + dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(1)
                            the_vars.append(X[j][k])
                            the_coefs.append(-1)
                            the_vars.append(X[i][k])
                            the_coefs.append(1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])
                        if (self._S[i][j] <= 0 and self._S[j][k] >= cut and self._S[i][k] >= 0):
                            # -dij  + djk  + dki <= 1
                            the_vars  = []
                            the_coefs = []
                            the_vars.append(X[i][j])
                            the_coefs.append(-1)
                            the_vars.append(X[j][k])
                            the_coefs.append(1)
                            the_vars.append(X[i][k])
                            the_coefs.append(1)
                            my_prob.linear_constraints.add(lin_expr = \
                                                           [cplex.SparsePair(the_vars, the_coefs)],
                                                           senses = ["L"], rhs = [1])

            # Save model
            if(model_file != None):
                my_prob.write(model_file)

            # Solve
            time_solver = my_prob.get_time()
            my_prob.solve()
            time_solver = my_prob.get_time() - time_solver

            # Number of constraints
            num_rows = my_prob.linear_constraints.get_num()

            # Number of Variables
            num_cols = my_prob.variables.get_num()

            # Objective value
            objective = my_prob.solution.get_objective_value()

            # Solution
            x = my_prob.solution.get_values()

            # Creating partition
            groups = []
            for i in range(self._n):
                groups.append(-1)

            groupID = 0
            for i in range(self._n):
                for j in range(self._n):
                    index = X[i][j]
                    if x[index] > 0:
                        # Both objects don't have group, put then together on a new
                        if groups[i] == -1 and groups[j] == -1:
                            groups[i] = groupID
                            groups[j] = groupID
                            groupID = groupID + 1
                        else:
                            # If i object don't have group put him on j group
                            if groups[i] == -1:
                                groups[i] = groups[j]
                            else:
                                groups[j] = groups[i]

            # The objects that remained alone create its own group
            for i in range(len(groups)):
                if groups[i] == -1:
                    groups[i] = groupID
                    groupID = groupID + 1
                        
            # Make solution object to return
            solution = {'num_rows':num_rows,
                        'num_cols':num_cols,
                        'objective':objective,
                        'time_solver':time_solver,
                        'heuristic':heuristic,
                        'groups':groups}
        
        except CplexError as exc:
            print (exc)
        
        return solution

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
        graph_positive.add_vertices(self._n)
        unique_positive_weights = set()
        for i in range(self._n):
            for j in range (i+1,self._n):
                if self._S[i][j] >= 0:
                    graph_positive.add_edge(i,j,weight=self._S[i][j])
                    unique_positive_weights.add(self._S[i][j])
        
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
        graph_negative.add_vertices(self._n)
        unique_negative_weights = set()
        for i in range(self._n):
            for j in range (i+1,self._n):
                if self._S[i][j] <= 0:
                    graph_negative.add_edge(i,j,weight=self._S[i][j])
                    unique_negative_weights.add(self._S[i][j])
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