package com.challengetotvs.api.security;

import com.challengetotvs.api.domain.consultor.Consultor;
import org.jspecify.annotations.Nullable;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;

public class ConsultorUserDetails implements UserDetails{

    private final Consultor consultor;

    public ConsultorUserDetails(Consultor consultor){
        this.consultor = consultor;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(new SimpleGrantedAuthority("ROLE_" + consultor.getRole()));
    }

    @Override
    public @Nullable String getPassword() {
        return consultor.getSenhaHash();
    }

    @Override
    public String getUsername() {
        return consultor.getEmail();
    }

    @Override
    public boolean isAccountNonExpired() {
        return UserDetails.super.isAccountNonExpired();
    }

    @Override
    public boolean isAccountNonLocked() {
        return UserDetails.super.isAccountNonLocked();
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return UserDetails.super.isCredentialsNonExpired();
    }

    public final Consultor getConsultor(){
        return consultor;
    }


}
