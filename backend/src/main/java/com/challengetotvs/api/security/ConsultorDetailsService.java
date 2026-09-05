package com.challengetotvs.api.security;

import com.challengetotvs.api.domain.consultor.ConsultorRepository;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class ConsultorDetailsService implements UserDetailsService {

    private final ConsultorRepository repository;

    public ConsultorDetailsService(ConsultorRepository repository){
        this.repository = repository;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        return repository.findByEmail(username)
                .map(ConsultorUserDetails::new)
                .orElseThrow(() -> new UsernameNotFoundException("Consultor não encontrado: " + username));
    }
}
