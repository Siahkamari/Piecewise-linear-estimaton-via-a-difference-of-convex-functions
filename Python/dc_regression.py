import numpy as np
import numpy.linalg as linalg
from tqdm import tqdm

class dc_regression:

    def __init__(self):
        self.y_hat = 0
        self.z = 0
        self.a = 0
        self.b = 0
        self.lanbda = 1

    def auto_tune(self, X, y):
        n_folds = 5

        lanbdas = [1e-3,1e-2,1e-1,1,1e1,1e2,1e3]

        while True:
            i = 0
            loss = np.zeros(len(lanbdas))
            for lanbda in tqdm(lanbdas):
                self.lanbda = lanbda
                loss[i] = self.cross_validate(X, y, n_folds)
                i += 1

            arg_min = np.argmin(loss)
            lanbda = lanbdas[arg_min]
            if  lanbda == lanbdas[0]:
                lanbdas = [i*lanbda for i in [1e-5,1e-4,1e-3,1e-2,1e-1,1,1e1]]
            elif lanbda == lanbdas[-1]:
                lanbdas = [i*lanbda for i in [1e-1,1,1e1,1e2,1e3,1e4,1e5]]
            else:
                if len(lanbdas) == 7:
                    lanbdas = [i*lanbda for i in [0.0625,0.125,0.25,0.5,1,2,4,8,16]]
                else:
                    self.lanbda = lanbda
                    self.fit(X, y, lanbda)
                    break

    def fit(self, X, y, lanbda = False, T = False):

        if lanbda == False:
            self.auto_tune(X, y)
            return
        else:
            self.lanbda = lanbda

        if T == False:
            T = 2*y.size

        n, dim = X.shape
        rho = 0.01
        T = 2*n

        # initial values
        # primal
        y_hat = np.zeros(n)
        z = np.zeros(n)
        a = np.zeros([n, dim])
        b = np.zeros([n, dim])
        p = np.zeros([n, dim])
        q = np.zeros([n, dim])

        L = 0

        # slack
        s = np.zeros([n, n])
        t = np.zeros([n, n])
        u = np.zeros([n, 1])

        # dual
        alpha = np.zeros([n, n])
        beta = np.zeros([n, n])
        gamma = np.zeros([n, 1])
        eta = np.zeros([n, dim])
        zeta = np.zeros([n, dim])

        # preprocess1
        XjXj = np.dot(X.T,X)
        Xbar = np.mean(X, axis = 0)
        ybar = np.mean(y)
        Sigma_i = np.zeros([n,dim,dim])

        for i in range(n):
            Sigma_i[i,:,:] = n*np.outer(X[i],X[i]) + XjXj - n*(np.outer(Xbar,X[i]) + np.outer(X[i],Xbar))
            Sigma_i[i,:,:] = linalg.inv(Sigma_i[i,:,:] + np.eye(dim))

        # ADMM iteration
        for iter in range(T):
            #   primal updates
            #   y_hat & z update
            # for i in range(n):
            #     y_hat[i] = 2/(2+n*rho) * y[i]
            #     z[i] = -1/(2+n*rho)*y[i]
            #     for j in range(n):
            #         temp1 = alpha[j,i] -  alpha[i,j] + s[j,i] - s[i,j] + np.dot(a[i] + a[j], X[i] - X[j]) + 2*y[j]
            #         temp2 = beta[j,i] - beta[i,j] + t[j,i] - t[i,j] + np.dot(b[i] + b[j], X[i] - X[j])

            #         y_hat[i] +=   rho/(2+n*rho)/2 * temp1  - rho/(2+n*rho)/2 * temp2
            #         z[i] += 1/(2*n)/(2+n*rho)* temp1 + (1+n*rho)/(2*n)/(2+n*rho)* temp2
    
            #   primal updates
            #   y_hat & z update
            temp1 = np.sum(alpha.T -  alpha + s.T - s -  np.dot(a,X.T) + np.dot(X,a.T), axis=1) + n*2*ybar + n*np.sum(a*X,axis=1) - np.sum(a*X)
            temp2 = np.sum(beta.T - beta + t.T - t - np.dot(b,X.T) + np.dot(X,b.T), axis=1) + n*np.sum(b*X, axis=1) - np.sum(b*X)

            y_hat = 2/(2+n*rho) * y +  rho/(2+n*rho)/2 * temp1  - rho/(2+n*rho)/2 * temp2
            z = -1/(2+n*rho)*y + 1/(2*n)/(2+n*rho)* temp1 + (1+n*rho)/(2*n)/(2+n*rho)* temp2

            # #   a update
            # for i in range(n):
            #     a[i] = p[i] - eta[i]
            #     for j in range(n):
            #         a[i] += (alpha[i,j] + s[i,j] + y_hat[i] - y_hat[j] + z[i] - z[j])*(X[i]-X[j])
            #     a[i] = np.matmul(Sigma_i[i], a[i])
            
            #   a update
            a = p - eta
            a += np.sum(alpha + s + y_hat.reshape(-1,1) - y_hat.reshape(1,-1) +\
             z.reshape(-1,1) - z.reshape(1,-1), axis=1).reshape(-1,1)*X -\
             np.dot(alpha + s + y_hat.reshape(-1,1) - y_hat.reshape(1,-1) +\
             z.reshape(-1,1) - z.reshape(1,-1), X)

            # for i in range(n):
            #     a[i] = np.matmul(Sigma_i[i,:,:], a[i])
            a = np.matmul(Sigma_i,a.reshape(n,dim,1)).reshape(n,dim)

            # #   b update
            # for i in range(n):
            #     b[i] = q[i] - zeta[i]
            #     for j in range(n):
            #         b[i] += (beta[i,j] + t[i,j] + z[i] - z[j])*(X[i]-X[j])
            #     b[i] = np.matmul(Sigma_i[i], b[i])
            
            #   b update
            b = q - zeta
            b += np.sum(beta + t + z.reshape(-1,1) - z.reshape(1,-1), axis=1).reshape(-1,1)*X - \
            np.dot(beta + t + z.reshape(-1,1) - z.reshape(1,-1), X)

            # for i in range(n):
            #     b[i] = np.matmul(Sigma_i[i,:,:], b[i])
            b = np.matmul(Sigma_i,b.reshape(n,dim,1)).reshape(n,dim)

            # #   p updates
            # for i in range(n):
            #     temp3 = 0
            #     for d in range(dim):
            #         temp3 += np.abs(p[i,d]) + np.abs(q[i,d])
            #     for d in range(dim):
            #         temp1 = 1/2* (a[i,d] + eta[i,d])
            #         temp2 = 1/2*(L - u[i] - gamma[i] + np.abs(p[i,d]) - temp3)
            #         p[i,d] = np.sign(temp1)*np.maximum(np.abs(temp1)+temp2, 0)

            #   p updates
            temp3 = np.sum(np.abs(p) + np.abs(q), axis=1).reshape(-1,1)
            temp1 = 1/2* (a + eta)
            temp2 = 1/2*(L - u - gamma + np.abs(p) - temp3)
            p = np.sign(temp1)*np.maximum(np.abs(temp1)+temp2, 0)

            # #   q updates
            # for i in range(n):
            #     temp3 = 0
            #     for d in range(dim):
            #         temp3 += np.abs(p[i,d]) + np.abs(q[i,d])
            #     for d in range(dim):
            #         temp1 = 1/2* (b[i,d] + zeta[i,d])
            #         temp2 = 1/2*(L - u[i] - gamma[i] + np.abs(q[i,d]) - temp3)
            #         q[i,d] = np.sign(temp1)*np.maximum(np.abs(temp1)+temp2, 0)

            #   q updates
            temp3 = np.sum(np.abs(p) + np.abs(q), axis=1).reshape(-1,1)
            temp1 = 1/2* (b + zeta)
            temp2 = 1/2*(L - u - gamma + np.abs(q) - temp3)
            q = np.sign(temp1)*np.maximum(np.abs(temp1)+temp2, 0)

            # #   L update
            # L = -1/(n*rho)* self.lanbda
            # for i in range(n):
            #     L +=  1/n*( gamma[i]  + u[i])
            #     for d in range(dim):
            #         L += 1/n* (np.abs(p[i,d]) +np.abs(q[i,d]))

            #   L update
            L = -1/(n*rho)* self.lanbda
            L +=  1/n*np.sum( gamma  + u)
            L += 1/n* np.sum(np.abs(p) +np.abs(q))
            
            #   slack updates
            #   s & t update
            # for i in range(n):
            #     for j in range(n):
            #         s[i,j] = -alpha[i,j] - y_hat[i] + y_hat[j] - z[i] + z[j] + np.dot(a[i], X[i]-X[j])
            #         s[i,j] = np.maximum(s[i,j] ,0)

            #         t[i,j] = -beta[i,j] - z[i] + z[j] + np.dot(b[i], X[i]-X[j])
            #         t[i,j] = np.maximum(t[i,j] ,0)

            s = - alpha -y_hat.reshape(-1,1) + y_hat.reshape(1,-1) - z.reshape(-1,1) + z.reshape(1,-1) + np.sum(a*X,axis=1).reshape(-1,1) - np.tensordot(a, X, axes=(1,1))
            s = np.maximum(s ,0)
            t = -beta - z.reshape(-1,1) + z.reshape(1,-1) + np.sum(b*X,axis=1).reshape(-1,1) - np.tensordot(b, X, axes=(1,1))
            t = np.maximum(t ,0) 

            #   u update
            u = -gamma + L
            u +=  np.sum(- np.abs(q) - np.abs(p), axis =1).reshape(-1,1)
            u = np.maximum(u, 0)

            # for i in range(n):
            #     u[i] = -gamma[i] + L
            #     for d in range(dim):
            #         u[i] +=  - np.abs(q[i,d]) - np.abs(p[i,d])
            #     u[i] = np.maximum(u[i], 0)
            
            #   dual updates
            # for i in range(n):
            #     for j in range(n):
            #         alpha[i,j] +=  s[i,j] + y_hat[i] - y_hat[j] + z[i] - z[j] - np.dot(a[i], X[i]-X[j])
            #         beta[i,j] +=  t[i,j] + z[i] - z[j] - np.dot(b[i], X[i]-X[j])

            alpha +=  s + y_hat.reshape(-1,1) - y_hat.reshape(1,-1) + z.reshape(-1,1) - z.reshape(1,-1) - np.sum(a*X,axis=1).reshape(-1,1) + np.dot(a, X.T)
            beta +=  t + z.reshape(-1,1) - z.reshape(1,-1) - np.sum(b*X,axis=1).reshape(-1,1) + np.dot(b, X.T)
        
            # for i in range(n):
            #     gamma[i] += u[i] - L 
            #     for d in range(dim):
            #         gamma[i] +=  np.abs(p[i,d]) + np.abs(q[i,d])
            #         eta[i,d] +=  a[i,d] - p[i,d]
            #         zeta[i,d] +=  b[i,d] - q[i,d]

            gamma += u - L 
            gamma += np.sum(np.abs(p) + np.abs(q), axis=1).reshape(-1,1)
            eta += a - p
            zeta += b - q

        y_hat = y_hat + z - np.sum(a*X, axis = 1)
        z = z - np.sum(b*X, axis = 1)

        self.y_hat = y_hat
        self.z = z
        self.a = a
        self.b = b
    
    def predict(self, X):
        pred =  np.max(self.y_hat.reshape(1,-1) + np.matmul(X,self.a.T), axis=1) - np.max(self.z.reshape(1,-1) + np.matmul(X,self.b.T), axis=1)

        return pred

    def cross_validate(self, X, y, n_folds):

        n, _ = X.shape

        # Permute the rows of X and y
        rp = np.random.permutation(n)
        y = y[rp]
        X = X[rp]

        # Initializing different measure
        loss = np.zeros(n_folds)

        for i in range(n_folds):
            
            # splitting the data to test and train
            test_start = int(np.ceil(n/n_folds * i))
            test_end = int(np.ceil(n/n_folds * (i+1)))

            I_test = [i for i in range(test_start, test_end)]
            I_train = [i for i in range(test_start)] + [i for i in range(test_end, n)] 
            
            # learning with the x_train and predicting with it
            self.fit(X[I_train], y[I_train], self.lanbda)
            
            y_hat_test = self.predict(X[I_test])
            loss[i] = np.mean((y_hat_test-y[I_test])**2)

        return np.mean(loss)
    


