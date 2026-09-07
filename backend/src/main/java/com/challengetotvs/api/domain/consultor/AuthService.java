package com.challengetotvs.api.domain.consultor;

import com.challengetotvs.api.security.ConsultorUserDetails;
import com.challengetotvs.api.security.JwtProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final ConsultorRepository repository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final JwtProvider jwtProvider;

    public void register(RegisterRequest request){
         if(repository.findByEmail(request.email()).isPresent()){
             throw new IllegalArgumentException("Email já está cadastrado");
         }

        var senha = passwordEncoder.encode(request.senha());

         var consultor = new Consultor(
                 request.nome(),
                 request.email(),
                 senha,
                 "CONSULTOR"
         );

         repository.save(consultor);
    }

    public AuthResponse login(LoginRequest request){
        var authToken = new UsernamePasswordAuthenticationToken(request.email(), request.senha());

        Authentication authentication;
        try {
            authentication = authenticationManager.authenticate(authToken);
        }catch (AuthenticationException exception){
            throw new BadCredentialsException("Login invalido!");
        }

        var userDetails = (ConsultorUserDetails) authentication.getPrincipal();
        var consultor = userDetails.getConsultor();

        var token = jwtProvider.generateToken(consultor.getEmail(), consultor.getRole());

        return new AuthResponse(token);
    }
}
